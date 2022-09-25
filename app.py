import PySimpleGUI as sg
sg.theme("DarkTeal2")
layout = [[sg.T("")], [sg.Text("Choose a folder: "), sg.Input(
    key="-INPUT_VALUE-", change_submits=True), sg.FolderBrowse(key="-FOLDER_PATH-")], [sg.Button("Submit")]]

###Building Window
window = sg.Window('My File Browser', layout, size=(600, 150))

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == "Exit":
        break
    elif event == "Submit":
        print("Folder path:", values["-FOLDER_PATH-"])
