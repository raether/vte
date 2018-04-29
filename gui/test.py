from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.gridlayout import GridLayout

# Create both screens. Please note the root.manager.current: this is how
# you can control the ScreenManager from kv. Each screen has by default a
# property manager that gives you the instance of the ScreenManager used.

Builder.load_string("""

<MenuScreen>:

    BoxLayout:
        orientation: 'vertical'
        
        BoxLayout:
            orientation: 'horizontal'
            Label:
                text: 'Video Traffic Enforcement'

        BoxLayout:
            orientation: 'horizontal'
            Label:
                text: 'Select View'
            Button:
                text: 'Left View'
                on_press: root.manager.current = 'left'
            Button:
                text: 'Front View'
                on_press: root.manager.current = 'front'
            Button:
                text: 'Rear View'
                on_press: root.manager.current = 'rear'
            Button:
                text: 'Quad View'
                on_press: root.manager.current = 'quad'
            Button:
                text: 'Settings'
                on_press: root.manager.current = 'settings'
            Button:
                text: 'Shutdown'

        BoxLayout:
            orientation: 'horizontal'
            Label:
                text: 'Unused Space'
 

<FrontScreen>:
    BoxLayout:
        Button:
            text: 'Front View'
            on_press: root.manager.current = 'menu'

<LeftScreen>:
    BoxLayout:
        Button:
            text: 'Left View'
            on_press: root.manager.current = 'menu'

<RearScreen>:
    BoxLayout:
        Button:
            text: 'Rear View'
            on_press: root.manager.current = 'menu'

<FrontQScreen>:
    BoxLayout:
        Button:
            text: 'Front View'
            on_press: root.manager.current = 'quad'

<LeftQScreen>:
    BoxLayout:
        Button:
            text: 'Left View'
            on_press: root.manager.current = 'quad'

<RearQScreen>:
    BoxLayout:
        Button:
            text: 'Rear View'
            on_press: root.manager.current = 'quad'


<QuadScreen>:
    GridLayout: 
        rows: 2
        cols: 2
        Button:
            text: 'Left View'
            on_press: root.manager.current = 'leftquad'
        Button:
            text: 'Front View'
            on_press: root.manager.current = 'frontquad'
        Button:
            text: 'Rear View'
            on_press: root.manager.current = 'rearquad'
        Button:
            text: 'Info View'
            on_press: root.manager.current = 'menu'

<SettingsScreen>:
    BoxLayout:
        Button:
            text: 'Settings View'
            on_press: root.manager.current = 'menu'

""")

# Declare screens
class MenuScreen(Screen):
    pass

class FrontScreen(Screen):
    pass

class LeftScreen(Screen):
    pass

class RearScreen(Screen):
    pass

class FrontQScreen(Screen):
    pass

class LeftQScreen(Screen):
    pass

class RearQScreen(Screen):
    pass

class QuadScreen(Screen):
    pass

class SettingsScreen(Screen):
    pass

# Create the screen manager
sm = ScreenManager()

sm.add_widget(MenuScreen(name='menu'))
sm.add_widget(FrontScreen(name='front'))
sm.add_widget(LeftScreen(name='left'))
sm.add_widget(RearScreen(name='rear'))
sm.add_widget(QuadScreen(name='quad'))
sm.add_widget(FrontQScreen(name='frontquad'))
sm.add_widget(LeftQScreen(name='leftquad'))
sm.add_widget(RearQScreen(name='rearquad'))
sm.add_widget(SettingsScreen(name='settings'))

class TestApp(App):

    def build(self):
	return sm

if __name__ == '__main__':
    TestApp().run()

