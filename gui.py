import PySimpleGUI as sg
from main import main as func
import subprocess
import os
from random import randint

APP_NAME = 'Member Decision'

class WindowTools:
    def __init__(self, title = '', layout = [[sg.Text('Sample')]]):
        self.layout = layout
        self.menu_def = [
            ['Menu', ['About {}'.format(APP_NAME)]],
        ]

        # Add MenuBar
        self.layout.insert(0, [sg.Menu(self.menu_def, font = sg.DEFAULT_FONT)])

        self.window = sg.Window(title, self.layout, font = ('Helvetica', 20), size = (1200, 675), element_justification='center', resizable = True)

    def read(self):
        self.event, self.values = self.window.read()
        if self.event == 'About {}'.format(APP_NAME):
            with open('about.txt', mode = 'r', encoding = 'utf_8') as f:
                lcns = f.read()
            sg.PopupOK(lcns, modal= False, keep_on_top= True, title = 'About {}'.format(APP_NAME))


sg.theme('Dark Blue 3')  # please make your creations colorful

main = WindowTools(layout = [
    [sg.Text()],
    [sg.Text('Member Decision', justification='center', font = ('Helvetica', 40))],
    [sg.Text()],
    [sg.Text('Select input file', size = (15, 1)), sg.InputText(visible = True, do_not_clear = False, key = '-INPUT_FILE-'), sg.FileBrowse()],
    [sg.Text('Select output folder', size = (15, 1)), sg.InputText(visible = True, do_not_clear = False, key = '-OUTPUT_FOLDER-'), sg.FolderBrowse()],
    [sg.Text()],
    [sg.Submit('Run'), sg.Cancel()],
    [sg.Text()],
    [sg.Frame('Options', [[sg.Text('seed', justification= 'center', size = (10, 1)), sg.InputText(None, key = 'seed', size = (7, 1))]], element_justification='center')],
])

popup_options = {
    'font': ('Helvetica', 20),
    'modal': False,
    'keep_on_top': True,
    }

while True:
    main.read()
    if main.event in (None, 'Cancel'):
        break
    elif main.event == 'Run':
        path_input = main.values['-INPUT_FILE-']
        dir_output = main.values['-OUTPUT_FOLDER-']
        if path_input == '':
            sg.PopupError('You have to select input file.', **popup_options)
        elif dir_output == '':
            sg.PopupError('You have to select output folder.', **popup_options)
        else:
            seed = randint(0, 2**32) if main.values['seed'] == 'None' else int(main.values['seed'])
            try:
                func(random_state = seed, path_input = path_input, dir_output = dir_output)
            except Exception as e:
                sg.PopupError(e, **popup_options)
            else:
                sg.PopupOK('Finish!', **popup_options)
                with open(os.path.join(dir_output, 'seed.txt'), mode = 'w', encoding = 'utf_8_sig') as f:
                    f.write('SEED: {}'.format(seed))
                subprocess.run(['open', dir_output])
            finally:
                break

main.window.close()
