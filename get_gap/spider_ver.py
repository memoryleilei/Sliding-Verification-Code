import time
from io import BytesIO
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image

EMAIL = 'cqc@cuiqingcai.com'
PASSWORD = '123456'
BORDER_1 = 7
BORDER_2 = 12


class CrackGeetest(object):

    def __init__(self):
        self.url = 'https://account.geetest.com/login'
        self.browser = webdriver.Chrome()
        self.browser.maximize_window()
        self.wait = WebDriverWait(self.browser, 5)
        self.email = EMAIL
        self.password = PASSWORD
        self.success = False
        self.try_num = 2
        self.now_num = 2
        self.flesh_num = 1

    def __del__(self):
        self.browser.close()

    # 获取初始验证按钮
    def get_geetest_button(self):
        """
        获取初始验证按钮
        :return:
        """
        button = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'geetest_radar_tip')))
        return button

    # 获取截图中验证码的上下左右的位置
    def get_position(self):
        """
        获取验证码位置
        :return: 验证码位置元组
        """
        img = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'geetest_canvas_img')))
        time.sleep(0.5)
        location = img.location
        size = img.size
        top, bottom, left, right = location['y'], location['y'] + size['height'], location['x'], location['x'] + size[
            'width']
        return top, bottom, left, right

    # 获取网页截图
    def get_screenshot(self):
        """
        获取网页截图
        :return: 截图对象
        """
        screenshot = self.browser.get_screenshot_as_png()
        screenshot = Image.open(BytesIO(screenshot))
        return screenshot

    # 获取滑块对象
    def get_slider(self):
        """
        获取滑块
        :return: 滑块对象
        """
        try:
            slider = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'geetest_slider_button')))
        except Exception:
            self.crack()
            return
        return slider

    # 获取验证码图片
    def get_geetest_image(self, name='captcha.png'):
        """
        获取验证码图片
        :return: 图片对象
        """
        top, bottom, left, right = self.get_position()
        screenshot = self.get_screenshot()
        captcha = screenshot.crop((left, top, right, bottom))
        captcha.save(name)
        return captcha

    # 打开页面,输入账号与密码
    def open(self):
        """
        打开网页输入用户名密码
        :return: None
        """
        self.browser.get(self.url)
        time.sleep(0.5)
        email = self.browser.find_elements_by_xpath("//i[@class='icon-email']/../../input")[0]
        password = self.browser.find_element_by_xpath("//i[@class='icon-password']/../../input")
        email.send_keys(self.email)
        password.send_keys(self.password)

    # 根据偏移量获取移动轨迹
    @staticmethod
    def get_track(distance):
        """
        根据偏移量获取移动轨迹
        :param distance: 偏移量
        :return: 移动轨迹
        """
        # 移动轨迹
        track = []
        # 当前位移
        current = 0
        # 减速阈值
        mid = distance * 4 / 5
        # 计算间隔
        t = 0.2
        # 初速度
        v = 0

        while current < distance:
            if current < mid:
                # 加速度为正2
                a = 2
            else:
                # 加速度为负3
                a = -3
            # 初速度v0
            v0 = v
            # 当前速度v = v0 + at
            v = v0 + a * t
            # 移动距离x = v0t + 1/2 * a * t^2
            move = v0 * t + 1 / 2 * a * t * t
            # 当前位移
            current += move
            # 加入轨迹
            track.append(round(move))
        return track

    # 拖动滑块到缺口处
    def move_to_gap(self, slider, track):
        """
        拖动滑块到缺口处
        :param slider: 滑块
        :param track: 轨迹
        :return:
        """
        ActionChains(self.browser).click_and_hold(slider).perform()
        for x in track:
            ActionChains(self.browser).move_by_offset(xoffset=x, yoffset=0).perform()
        time.sleep(0.5)
        ActionChains(self.browser).release().perform()

    # 获取缺口偏移量
    def get_gap(self, image):
        """
        获取缺口偏移量
        :param image: 带缺口图片
        :return:
        """
        left_list = []
        for i in [10 * i for i in range(1, 14)]:
            for j in range(50, image.size[0] - 30):
                if self.is_pixel_equal(image, j, i, left_list):
                    break
        return left_list

    # 判断缺口偏移量
    @staticmethod
    def is_pixel_equal(image, x, y, left_list):
        """
        判断两个像素是否相同
        :param image: 图片
        :param x: 位置x
        :param y: 位置y
        :return: 像素是否相同
        """
        x_max = image.size[0]
        # 取两个图片的像素点
        pixel1 = image.load()[x, y]
        threshold = 150
        count = 0
        if pixel1[0] < threshold and pixel1[1] < threshold and pixel1[2] < threshold:
            for i in range(x + 1, image.size[0]):
                piexl = image.load()[i, y]
                if piexl[0] < threshold and piexl[1] < threshold and piexl[2] < threshold:
                    count += 1
                else:
                    break
        if int(x_max/8.6) < count < int(x_max/4.3):
            left_list.append((x, count))
            return True
        else:
            return False

    def crack(self):
        # 输入用户名密码
        self.open()

        # 点击验证按钮
        time.sleep(1)
        button = self.get_geetest_button()
        button.click()

        # ＢOREDER有俩种情况，一种是７,一种是１４
        def slider_try(gap, BORDER):
            if self.now_num:
                # 减去缺口位置
                gap -= BORDER
                # 计算滑动距离
                track = self.get_track(int(gap))

                # 拖动滑块
                slider = self.get_slider()
                self.move_to_gap(slider, track)
                try:
                    self.success = self.wait.until(
                        EC.text_to_be_present_in_element((By.CLASS_NAME, 'geetest_success_radar_tip_content'), '验证成功'))
                except Exception as e:
                    self.now_num -= 1
                    test_num = self.try_num - self.now_num
                    if self.now_num == 0:
                        print("第%d次尝试失败, 验证失败" % test_num)
                    else:
                        print("验证失败,正在进行第%d次尝试" % test_num)

        while not self.success and self.now_num > 0:

            # 获取验证码图片
            try:
                image = self.get_geetest_image()
            except Exception as e:
                # todo: 判断是其他验证，或者是自动识别通过
                self.success = True
                print("自动识别通过，无需滑动%s" % e)
                time.sleep(5)
                return

            # 获取缺口位置
            left_list = self.get_gap(image)
            x_max = image.size[0]
            left_list = sorted(left_list, key=lambda x: abs(x[1]-int(x_max/6.45)))
            print(left_list)
            if not left_list:
                print("left_lsit为空, 无法获取gap")
                break
            gap = left_list[0][0]

            # 第一中请求，gap减少７
            slider_try(gap, BORDER_1)
            # 成功后退出
            if not self.success:
                # 尝试gap减少14
                slider_try(gap, BORDER_2)
            if self.success:
                test_num = self.try_num - self.now_num + 1
                print("第{}次刷新,第{}次尝试,验证通过".format(self.flesh_num, test_num))
                time.sleep(5)
                self.success = True

        if not self.success:
            print("重新刷新页面,这是第%d次刷新" % self.flesh_num)
            self.flesh_num += 1
            self.now_num = 2
            self.try_num = 2
            self.crack()


if __name__ == '__main__':
    crack = CrackGeetest()
    crack.crack()
    del crack
