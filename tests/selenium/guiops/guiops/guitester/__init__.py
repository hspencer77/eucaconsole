from selenium import webdriver
from guiops.pages.basepage import BasePage
from guiops.pages.loginpage import LoginPage
from guiops.utilities import Utilities


class GuiTester(Utilities):
        def __init__(self, webdriver_url, console_url, account= "ui-test-acct-00", user= "admin", password= "mypassword0"):
            self.driver = webdriver.Remote(webdriver_url, webdriver.DesiredCapabilities.FIREFOX)
            self.driver.implicitly_wait(60)
            self.driver.maximize_window()
            self.driver.get(console_url)
            self.account=account
            self.user=user
            self.password=password

        def set_implicit_wait(self,time_to_wait):
            self.driver.implicitly_wait(time_to_wait=time_to_wait)

        def login(self):
            LoginPage(self).login()

        def logout(self):
            BasePage(self).logout()



