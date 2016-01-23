import os
from selenium import webdriver
from pyvirtualdisplay import Display

display = Display(visible=0, size=(800, 600))
display.start()
driver = webdriver.Chrome()
driver.get("http://www.google.com")
print(driver.page_source.encode('utf-8'))
driver.quit()
display.stop()