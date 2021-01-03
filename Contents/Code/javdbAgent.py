import urllib2
import ssl
import re
from datetime import datetime
from lxml import html

SEARCH_URL = 'https://javdb.com/search?q=%s'
curID = "javdb"


def getElementFromUrl(url):
    return html.fromstring(request(url))

def request(url):
    user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
    headers = {'User-Agent': user_agent, }
    request = urllib2.Request(url, headers=headers)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return urllib2.urlopen(request, context=ctx).read()


def elementToString(ele):
    html.tostring(ele, encoding='utf8')


def search(query, results, media, lang):
    try:
        url = str(SEARCH_URL % query)
        for movie in getElementFromUrl(url).xpath('//div[contains(@class,"grid-item")]'):
            movieid = movie.xpath('//div[contains(@class,"uid")]')
            Log(movieid)
            results.Append(MetadataSearchResult(id=curID + "|" + str(movieid),
                                                name=str(movieid.split('ja_')[1]+" - JavDB"), score=100, lang=lang))
        results.Sort('score', descending=True)
        Log(results)
    except Exception as e:
        Log(e)


def update(metadata, media, lang):
    if curID != str(metadata.id).split("|")[0]:
        return

    query = str(metadata.id).split("|")[1].replace('_', '/', 4)
    if re.search('\d{4}-\d\d-\d\d$', query):
        query = query.replace('/ja', '')
    Log('Update Query: %s' % str(query))
    try:
        movie = getElementFromUrl(query).xpath('//div[@class="container"]')[0]
        Log('Find Movie: %s' % html.tostring(movie, encoding='unicode'))

        # title
        if movie.xpath('.//h3'):
            metadata.title = movie.xpath('.//h3')[0].text_content().strip()

        # poster
        image = movie.xpath('.//a[contains(@class,"bigImage")]')[0]
        thumbUrl = image.get('href')
        thumb = request(thumbUrl)
        posterUrl = image.get('href')
        metadata.posters[posterUrl] = Proxy.Preview(thumb)

        # actors
        metadata.roles.clear()
        for actor in movie.xpath('.//a[@class="avatar-box"]'):
            img = actor.xpath('.//img')[0]
            role = metadata.roles.new()
            role.name = img.get("title")
            role.photo = img.get("src")
            metadata.collections.add(role.name)
            Log('Actor: %s' % role.name)

        # release date & year
        moviedate = movie.xpath('.//p')[1].text_content().strip().replace(
            '???: ', '').replace('Release Date: ', '').replace('????: ', '')
        metadata.originally_available_at = datetime.strptime(
            moviedate, '%Y-%m-%d')
        metadata.year = metadata.originally_available_at.year
        Log('Found Date: %s' % metadata.originally_available_at)

        # studio
        studio = movie.xpath(
            './/p')[4].text_content().strip().replace('????: ', '')
        Log('Studio Found: %s' % studio)
        metadata.studio = studio

        # genres
        genres = movie.xpath('.//span[@class="genre"]')
        if len(genres) > 0:
            metadata.genres.clear()
            for genreLine in genres:
                metadata.genres.add(genreLine.text_content().strip())
        Log("ok %s" % genres)

    except Exception as e:
        Log(e)
