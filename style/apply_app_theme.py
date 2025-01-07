import os

def apply_app_theme(MainWindow, app, app_path, stylesheet):

    app.setStyle("Fusion")
    with open(os.path.join(app_path, "style", stylesheet), "r") as file:
        stylesheet = file.read()
    app.setStyleSheet(stylesheet)
    MainWindow.toolbar.setStyleSheet(stylesheet)