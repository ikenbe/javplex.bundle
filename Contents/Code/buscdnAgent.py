import urllib2
import ssl
from datetime import datetime
from lxml import html



SEARCH_URL = 'https://www.buscdn.life/ja/search/%s'
curID = "buscdn"

def getElementFromUrl(url):
    return html.fromstring(request(url))

def request(url):
    user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
    headers={'User-Agent':user_agent,} 
    #url="https://www.buscdn.life"
    Log('Search Query: %s' % url)
    request = urllib2.Request(url,headers=headers)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    #Log(urllib2.urlopen(request,context=ctx).read())
    return urllib2.urlopen(request,context=ctx).read()

def elementToString(ele):
    html.tostring(ele, encoding='unicode')

def search(query, results, media, lang):
    try:
        url=str(SEARCH_URL % query)
        for movie in getElementFromUrl(url).xpath('//a[contains(@class,"movie-box")]'):
            movieid = movie.get("href").replace('/',"_")
            results.Append(MetadataSearchResult(id= curID + "|" + str(movieid), name=str(movieid.split('ja_')[1]+" - JavBus"), score=100,lang=lang))
            
        results.Sort('score', descending=True)
        Log(results)
    except Exception as e: Log(e)


def update(metadata, media, lang): 
    if curID != str(metadata.id).split("|")[0]:
        return

    query = str(metadata.id).split("|")[1].replace('_','/')
    Log('Update Query: %s' % str(query))
    try:
        movie = getElementFromUrl(query).xpath('//div[@class="container"]')[0]
        #Log('Find Movie: %s' % elementToString(movie))
	    Log('Find Movie: %s' % html.tostring(movie, encoding='UTF-8'))

        #title
        if movie.xpath('.//h3'):
            metadata.title = movie.xpath('.//h3')[0].text_content().strip()
        
        
	   #poster
        image = movie.xpath('.//a[contains(@class,"bigImage")]')[0]
        thumbUrl = 'https://images.weserv.nl/?url='+image.get('href')+'&w=375&h=536&fit=cover&a=right'
        thumb = request(thumbUrl)
        posterUrl = 'https://images.weserv.nl/?url='+image.get('href')+'&w=375&h=536&fit=cover&a=right'
        metadata.posters[posterUrl] = Proxy.Preview(thumb)

        #actors
        metadata.roles.clear()
        
	    for actor in  movie.xpath('.//a[@class="avatar-box"]'):
            img = actor.xpath('.//img')[0]
            role = metadata.roles.new()
            role.name = img.get("title")
            role.photo = img.get("src")
            Log('Actor: %s' % role.name)

	    Log('Start finding date')
        #originally_available_at
        #moviedate = movie.xpath('.//div[@class="info"]')
	    moviedate = movie.xpath('.//p')[1].text_content().strip().replace('発売日: ','').replace('Release Date: ','')
	    metadata.originally_available_at = datetime.strptime(moviedate,'%Y-%m-%d')
	    metadata.year = metadata.originally_available_at.year
        Log('Found Date: %s' % metadata.originally_available_at)


    except Exception as e: Log(e)
