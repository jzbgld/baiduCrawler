#!/bin/python
# -*-coding: utf-8-*-

import urllib
import requests
import re
import xlwt
import sys


class baidu_Search:
    def __init__(self):
        # loop control
        self.enable = True
        # search result page count
        self.page = 0
        # result count
        self.count = 0
        # define the output split
        self.sheetSplit = 30
        self.sheetPage = 0
        self.maxCount = 100

    # remove empty tags
    def rmTags(self, str):
        pattern1 = re.compile(r'<.*?>', re.DOTALL)
        pattern2 = re.compile(r'&nbsp')
        pattern3 = re.compile(ur';-;')
        pattern4 = re.compile(ur'&gt;\s*')
        str = pattern1.sub('', str)
        str = pattern2.sub('', str)
        str = pattern3.sub(u',', str)
        str = pattern4.sub(u'', str)
        return str

    # parse baidu url to real url
    # add exception
    def getRealUrl(self, fakeUrl):
        try:
            res = requests.get(fakeUrl, timeout=20)
            return res.url
        except requests.exceptions.Timeout:
            return fakeUrl

    # get baidu result page counts
    def getPageCounts(self, htmlunicode):
        # <div class="nums">百度为您找到相关结果约68,900,000个</div>
        pattern = re.compile(r'<div class="nums">.+?</div>(.*?)</div>')
        m = pattern.search(htmlunicode)
        pagesCount = ''
        if m:
            pagesCount = m.group(1)
        else:
            print u'未查询到任何结果!'
            self.enable = False
        return pagesCount

    # get next page url
    # this is the standard method
    def getNextPageUrl(self, htmlunicode):
        # learned find sth by layer
        pattern = re.compile(r'<div id="page"\s*>.*?<strong>.*?</strong><a href="(.*?)">')
        m = pattern.search(htmlunicode)
        nextPageUrl = ''
        if m:
            nextPageUrl = 'http://www.baidu.com' + m.group(1)
        else:
            print u"未找到下一页!"
        return nextPageUrl

    # get title and abstracts
    def getTitles_Abstracts(self, htmlunicode):
        patternResults = re.compile(
                r'<div class="result c-container\s*".*?><h3 class="t"\s*>.*?<div class="c-abstract"\s*>.*?</div>',
                re.DOTALL)
        # findall在无分组时返回元素为整个匹配字符串的list,在有分组时返回tuple类型的list
        m = patternResults.findall(htmlunicode)
        titles_abstracts = []
        if (m):
            # print m
            for result in m:
                patternTA = re.compile(r'<h3 class="t"\s*>(.*?)</h3>.*?<div class="c-abstract">(.*?)</div>', re.DOTALL)
                # patternUrl = re.compile(r'<h3 class="t"\s*><a.*?href="(.*?)".*?</a></h3>',re.MULTILINE)
                patternUrl = re.compile(r'href.*?=.*?"(.*?)"', re.DOTALL)
                mTA = patternTA.search(result)
                mUrl = patternUrl.search(mTA.string)
                if (mTA):
                    title = self.rmTags(mTA.group(1))
                    abstract = self.rmTags(mTA.group(2))
                    newsurl = self.getRealUrl(mUrl.group(1))
                    titles_abstracts.append((title, abstract, newsurl))
                else:
                    titles_abstracts.append((u'没有标题', u'没有摘要', u'空链接'))
        else:
            print u'未匹配到标题和摘要!'
        return titles_abstracts

    # rewrite baidu search by requests
    def Search(self, kw):
        # kw = kw.decode(sys.stdin.encoding).encode('utf-8')
        searchurl = 'http://www.baidu.com/' + 's?ie=utf-8&wd=' + urllib.quote(kw)
        resp = requests.get(searchurl)
        htmlunicode = resp.text

        # write to excel workbook
        outputBook = xlwt.Workbook(encoding='utf-8', style_compression=0)
        # add the first sheet
        sheetName = 'news' + str(self.sheetPage + 1)
        outputSheet = outputBook.add_sheet(sheetName, cell_overwrite_ok=True)
        # write the first line
        outputSheet.write(0, 0, u"标题")
        outputSheet.write(0, 1, u"摘要")
        outputSheet.write(0, 2, u"链接")

        pagesCount = self.getPageCounts(htmlunicode)
        print pagesCount

        while self.enable:
            print u'正在处理第', self.page + 1, '页内容，没有更多结果程序会自动退出：'
            # print u'请按[回车键]浏览第', self.page + 1, '页内容,输入[quit]退出程序:'
            # myInput = raw_input()
            # if (myInput == 'quit'):
            #     break
            titles_abstracts = self.getTitles_Abstracts(htmlunicode)

            for index in range(len(titles_abstracts)):
                print u"第", self.page + 1, "页第", index + 1, "个搜索结果..."
                print u'写入第', self.count + 1, u'个结果.'
                print u"标题: ", titles_abstracts[index][0]
                print u"摘要: ", titles_abstracts[index][1]
                print u"链接: ", titles_abstracts[index][2]
                # add new sheet
                if (self.count != 0) and (self.count % self.sheetSplit == 0):
                    self.sheetPage += 1
                    sheetName = 'news' + str(self.sheetPage + 1)
                    outputSheet = outputBook.add_sheet(sheetName, cell_overwrite_ok=True)
                    # write the first line
                    outputSheet.write(0, 0, u"标题")
                    outputSheet.write(0, 1, u"摘要")
                    outputSheet.write(0, 2, u"链接")

                outputRow = self.count % self.sheetSplit + 1
                outputSheet.write(outputRow, 0, titles_abstracts[index][0])
                outputSheet.write(outputRow, 1, titles_abstracts[index][1])
                outputSheet.write(outputRow, 2, titles_abstracts[index][2])
                self.count += 1
                print "\r\n"

            nextPageUrl = self.getNextPageUrl(htmlunicode)
            self.page += 1
            # print u'下一页url为:', nextPageUrl
            if (nextPageUrl == '') or (self.count > self.maxCount):
                break

            resp = requests.get(nextPageUrl)
            htmlunicode = resp.text

        # save to file
        outputBook.save('.\output\output.xls')


if __name__ == '__main__':
    print u"""
    --------------------------------------------
        howTo : enter "quit" to quit program
        advert: 按下任意键来浏览,按下quit退出
    --------------------------------------------
    """
    myBaidu = baidu_Search()
    # myBaidu.Search('红帽CloudForms 4:混合云管理的里程碑')
    myBaidu.Search(raw_input(u'enter keyword to search: '))
