from selenium.webdriver.remote.webelement import WebElement


def element(css=None, *, link_text=None):
    '''
    An element property, to be defined in a Page class.
    For example:

    class FooPage(Page):
        admin_login_link = element(link_text='Election operators login here')
        login_button = element('input[value=Login]')

        def click_login_button(self):
            self.login_button.click()
    '''

    def getter(self) -> WebElement:
        if css:
            return self.driver.find_element_by_css_selector(css)
        elif link_text:
            return self.driver.find_element_by_link_text(link_text)
        else:
            raise Exception('unknown selector')
    return property(getter)


class Page:
    url = None

    def __init__(self, driver, site_url):
        self.driver = driver
        self.site_url = site_url

    def verify(self):
        '''
        Verify that we are on this page.
        '''
        assert self.driver.current_url == self.site_url + self.url

    def should_be_on_page(self, page_cls) -> 'Page':
        '''
        Verify that we have entered a new page. Construct that page and return
        it.
        '''
        page = page_cls(self.driver, self.site_url)
        page.verify()
        return page


class MainPage(Page):
    url = '/'
    admin_login_link = element(link_text='Election operators login here')

    def click_login(self):
        self.admin_login_link.click()
        return self.should_be_on_page(LoginPage)


class LoginPage(Page):
    url = '/auth/auth/login'
    username = element('#id_username')
    password = element('#id_password')
    login_button = element('input[value=Login]')

    def fill(self, username, password):
        self.username.send_keys(username)
        self.password.send_keys(password)

    def click_login(self):
        self.login_button.click()


class CreateElectionPage(Page):
    url = '/elections/new'
