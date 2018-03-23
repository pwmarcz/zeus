from .pages import CreateElectionPage


def test_login(main_page, config):
    login_page = main_page.click_login()
    login_page.fill(config['admin_username'], config['admin_password'])
    login_page.click_login()
    login_page.should_be_on_page(CreateElectionPage)
