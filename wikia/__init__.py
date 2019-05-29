import requests
from urllib.parse import urljoin
import json
from enum import Enum


class DefaultNamespaces:
    Media = -2,
    Special = -1,
    Main = 0,
    Talk = 1,
    User = 2,
    UserTalk = 3,
    pr_Community_Central = 4,
    pr_Talk_Community_Central = 5,
    File = 6,
    FileTalk = 7,
    MediaWiki = 8,
    MediaWikiTalk = 9,
    Template = 10,
    TemplateTalk = 11,
    Help = 12,
    HelpTalk = 13,
    Category = 14,
    CategoryTalk = 15,
    Forum = 110,
    ForumTalk = 111


class GetActivityBy(Enum):
    LatestActivity = "/Activity/LatestActivity"
    RecentlyChangedArticles = "/Activity/RecentlyChangedArticles"


class GetArticlesBy(Enum):
    Abc_order = "/Articles/List"
    New = "/Articles/New"
    Popular = "/Articles/Popular"
    Top = "/Articles/Top"


class Activity:

    def __init__(self, originWiki=None, articleid=0, userid=0, revisionId=3401438, timestamp=1558477400):
        self.originWiki = originWiki
        self.articleid = articleid
        self.userid = userid
        self.revisionId = revisionId
        self.timestamp = timestamp

    def User(self):
        return User.GetFromId(self.originWiki, self.userid)

    def Article(self):
        return Article.GetFromId(self.originWiki, self.articleid)


class User:

    def __init__(self, originWiki=None, userid=0, title="", name="", url="", numberofedits=0, avatar=""):
        self.originWiki = originWiki
        self.userid = userid
        self.title = title
        self.name = name
        self.url = urljoin(originWiki.uri, url)
        self.numberofedits = numberofedits
        self.avatar = avatar

    @staticmethod
    def GetFromId(originWiki, ID):
        userjson = requests.get(
            originWiki.apiurl + '/User/Details',
            params={
                'ids': str(ID)
            }
        ).content.decode()
        userjson = json.loads(userjson)['items'][0]
        return User(
            originWiki=originWiki,
            userid=userjson['user_id'],
            title=userjson['title'],
            name=userjson['name'],
            url=userjson['url'],
            numberofedits=userjson['numberofedits'],
            avatar=userjson['avatar']
        )


class Article:

    def __init__(self, originWiki=None, ID=0, title="", url="", namespace=None):
        self.originWiki = originWiki
        self.ID = ID
        self.title = title
        self.url = urljoin(originWiki.uri, url)
        self.namespace = namespace

    @staticmethod
    def GetFromId(originWiki, ID):
        articlejson = requests.get(
            originWiki.apiurl + '/Articles/Details',
            params={
                'ids': str(ID)
            }
        ).content.decode()
        articlejson = json.loads(articlejson)['items'][str(ID)]
        return Article(
            originWiki=originWiki,
            ID=articlejson['id'],
            title=articlejson['title'],
            url=articlejson['url'],
            namespace=articlejson['ns']
        )

    def GetRelated(self, limit=3):
        related_articles = []

        article_json = requests.get(
            self.originWiki.apiurl + '/RelatedPages/List',
            params={
                'ids': self.ID,
                'limit': str(limit)
            }
        ).content.decode()

        article_json = json.loads(article_json)['items']
        for article_data in article_json:
            related_articles.append(
                Article(
                    originWiki=self.originWiki,
                    ID=article_data['id'],
                    url=article_data['url'],
                    title=article_data['title']
                )
            )

    def GetInfo(self):
        info_json = requests.get(
            self.originWiki.apiurl + '/Articles/Details',
            params={
                'ids': str(self.ID)
            }
        ).content.decode()
        info_json = json.loads(info_json)['items']
        return ArticleInfo(
            commentNum=info_json['comments'],
            type=info_json['type'],
            abstract=info_json['abstract'],
            thumbnail=info_json['thumbnail'],
            original_dimensions=(info_json['original_dimensions']['width'], info_json['original_dimensions']['height'])
        )


class ArticleInfo:

    def __init__(self, commentNum, type, abstract, thumbnail, original_dimensions):
        self.commentNum = commentNum
        self.type = type
        self.abstract = abstract
        self.thumbnail = thumbnail
        self.original_dimensions = original_dimensions


class WikiStats:

    def __init__(self, edits, articles, pages, users, activeUsers, images, videos, admins, discussions):
        self.edits = edits
        self.articles = articles
        self.pages = pages
        self.users = users
        self.activeUsers = activeUsers
        self.images = images
        self.videos = videos
        self.admins = admins
        self.discussions = discussions


class Wiki:

    def __init__(self, wikiname="", ID=0, hub="", language="", topic="", domain=""):
        self.wikiname = wikiname
        self.ID = ID
        self.hub = hub
        self.language = language
        self.topic = topic
        self.domain = domain
        self.uri = "https://" + domain + '/'
        self.apiurl = self.uri + "/api/v1/"

    def GetActivity(self, by=GetActivityBy.LatestActivity, limit=10, allowduplicates=False):
        activity = []

        activity_json = requests.get(
            self.apiurl + by.value,
            params={
                'limit': str(limit),
                'allowDuplicates': str(allowduplicates).lower()
            }
        ).content.decode()
        activity_json = json.loads(activity_json)['items']
        for activity_data in activity_json:
            activity.append(
                Activity(
                    originWiki=self,
                    articleid=activity_data['article'],
                    userid=activity_data['user'],
                    revisionId=activity_data['revisionId'],
                    timestamp=activity_data['timestamp']
                )
            )
        return activity

    def GetArticles(self, by=GetArticlesBy.Abc_order, namespace=None, category="", limit=10, baseArticleId=None):
        articles = []

        article_json = requests.get(
            self.apiurl + by.value,
            params={
                limit: str(limit),
            }
        ).content.decode()
        articledatalist = json.loads(article_json)['items']
        for articledata in articledatalist:
            articles.append(
                Article(
                    originWiki=self,
                    ID=articledata['id'],
                    title=articledata['title'],
                    url=articledata['url'],
                    namespace=articledata['ns']
                )
            )
        return articles

    def GetStats(self):
        stats_json = requests.get(
            self.apiurl + "/Wikis/Details",
            params={
                'ids': str(self.ID)
            }
        ).content.decode()

        stats_data = json.loads(stats_json)['items'][str(self.ID)]
        return WikiStats(
            edits=stats_data['edits'],
            articles=stats_data['articles'],
            pages=stats_data['pages'],
            users=stats_data['users'],
            activeUsers=stats_data['activeUsers'],
            images=stats_data['images'],
            videos=stats_data['videos'],
            admins=stats_data['admins'],
            discussions=stats_data['discussions']
        )

    @staticmethod
    def SearchWikis(name="", hub="", lang="en", limit=25, batch=1, include_domain=True):
        wikis = []

        search_json = requests.get(
            "https://community.fandom.com/api/v1/Wikis/ByString",
            params={
                'string': name,
                'hub': hub,
                'lang': lang,
                'limit': str(limit),
                'batch': str(batch),
                'includeDomain': str(include_domain).lower()
            }
        ).content.decode()
        # using .content.decode() instead of .text will solve most
        # encoding errors
        search_json = json.loads(search_json)
        for wikidata in search_json['items']:
            wikis.append(
                Wiki(
                    wikiname=wikidata['name'],
                    ID=wikidata['id'],
                    hub=wikidata['hub'],
                    language=wikidata['language'],
                    topic=wikidata['topic'],
                    domain=wikidata['domain']
                )
            )
        return wikis