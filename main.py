import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QLineEdit, QPushButton, QMessageBox, QScrollArea, QFileDialog, QShortcut
from PyQt5.QtGui import QPixmap, QPainter, QPen, QFont, QPainterPath, QKeySequence
from PyQt5.QtCore import Qt, QRectF, QPointF
import xml.etree.ElementTree as ET
import numpy as np
import json
from PIL import Image

class TextlineEditorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        ##self.textlines = textlines  # List of {"coords": [(x1, y1), (x2, y2), ...], "text": "text"}
        self.selected_textline = None  # Currently selected textline for editing
        self.highlighted_textline = None  # Textline being highlighted during mouse movement
        self.init_ui()
        self.return_textline_of_xml()

    def init_ui(self):
        
        self.image_path = QFileDialog.getOpenFileName(
            self, "Select Image File", "", "Image Files (*.png *.jpg *.jpeg *.bmp *tif *tiff)"
        )[0]

        if not self.image_path:
            QMessageBox.warning(self, "Error", "No image selected!")
            sys.exit()
            
            
        self.xml_path = QFileDialog.getOpenFileName(
            self, "Select xml File", "", "xml Files (*.xml)"
        )[0]

        if not self.xml_path:
            QMessageBox.warning(self, "Error", "No image selected!")
            sys.exit()
            
            
        if self.image_path.lower().endswith(('.tif', '.tiff')):
            tiff_image = Image.open(self.image_path)
            tiff_image.save("temp_image.png")
            self.pixmap = QPixmap("temp_image.png")
        else:
            self.pixmap = QPixmap(self.image_path)
    
    
    
    
        image_width = self.pixmap.width()
        image_height = self.pixmap.height()
        
        
        # Get the screen size
        screen_size = QApplication.primaryScreen().availableGeometry()
        screen_width = screen_size.width()
        screen_height = screen_size.height()

        # Scale the image if it exceeds the screen size
        if image_width > screen_width or image_height > screen_height:
            scale_factor = min(screen_width / image_width, screen_height / image_height)
            self.pixmap = self.pixmap.scaled(
                int(image_width * scale_factor),
                int(image_height * scale_factor),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            

        
        self.setWindowTitle("Textline Editor")
        self.resize(screen_width, screen_height)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        
        #self.setGeometry(100, 100, image_width, image_height)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area)

        # Image label with mouse tracking enabled
        self.image_label = QLabel(self)
        self.image_label.setMouseTracking(True)  # Enable mouse tracking
        self.image_label.setPixmap(self.pixmap)
        self.image_label.mouseMoveEvent = self.on_mouse_move
        self.image_label.mousePressEvent = self.on_mouse_press

        # Set the image label as the widget inside the scroll area
        self.scroll_area.setWidget(self.image_label)

        self.text_bar = QLabel(self)
        self.text_bar.setAlignment(Qt.AlignLeft)
        self.text_bar.setFixedHeight(80)
        self.text_bar.setStyleSheet("background-color: lightgray; font-size: 30px; padding: 10px;")
        self.text_bar.setText("Hover over a textline to see its content.")
        self.layout.addWidget(self.text_bar)

        # Text editor for editing textlines
        self.text_edit = QLineEdit(self)
        #self.text_edit.setFixedHeight(100)  # Adjust the height of the text input field
        #self.text_edit.setFont(QFont("Arial", 30))  # Increase font size for better readability
        self.text_edit.hide()
        self.layout.addWidget(self.text_edit)

        # Save button for saving changes
        self.save_button = QPushButton("Save Changes", self)
        self.save_button.hide()
        self.save_button.clicked.connect(self.save_text)
        self.layout.addWidget(self.save_button)
        
        
        # Shortcut for saving (Ctrl+S)
        self.save_shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_S), self)
        self.save_shortcut.activated.connect(self.save_text)  # Connect the shortcut to the save function
        
        # Save All Textlines button
        self.save_all_button = QPushButton("Save All Textlines to File", self)
        self.save_all_button.clicked.connect(self.save_all_textlines)
        self.layout.addWidget(self.save_all_button)
        
        # Keyboard shortcuts for resizing the text editor only (Ctrl + and Ctrl -)
        self.zoom_in_shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Plus), self)
        self.zoom_in_shortcut.activated.connect(self.zoom_in)

        self.zoom_out_shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Minus), self)
        self.zoom_out_shortcut.activated.connect(self.zoom_out)
        
        # Add a menu for changing input files
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")

        change_input_action = file_menu.addAction("Change Input")
        change_input_action.triggered.connect(self.reload_data)

        # Add a button for changing input (if preferred over menu)
        self.change_input_button = QPushButton("Change Input", self)
        self.change_input_button.clicked.connect(self.reload_data)
        self.layout.addWidget(self.change_input_button)
    
    
    def reload_data(self):
        """Reload the input image and XML file."""
        image_path = QFileDialog.getOpenFileName(
            self, "Select Image File", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)"
        )[0]
        if image_path:
            self.image_path = image_path
            if image_path.lower().endswith(('.tif', '.tiff')):
                tiff_image = Image.open(self.image_path)
                tiff_image.save("temp_image.png")
                self.pixmap = QPixmap("temp_image.png")
            else:
                self.pixmap = QPixmap(self.image_path)

        xml_path = QFileDialog.getOpenFileName(
            self, "Select XML File", "", "XML Files (*.xml)"
        )[0]
        if xml_path:
            self.xml_path = xml_path
            #self.return_textline_of_xml()  # Reload textlines from the new XML file

        # Update the UI with the new data
        self.image_label.setPixmap(self.pixmap)
        self.textlines = []  # Reset textlines
        self.return_textline_of_xml()  # Load textlines for the new file
        
    def zoom_in(self):
        """Increase the font size of the text editor only."""
        current_font = self.text_edit.font()
        current_font_size = current_font.pointSize()
        new_font_size = current_font_size + 2  # Increase by 2 points
        current_font.setPointSize(new_font_size)
        self.text_edit.setFont(current_font)

    def zoom_out(self):
        """Decrease the font size of the text editor only."""
        current_font = self.text_edit.font()
        current_font_size = current_font.pointSize()
        new_font_size = max(current_font_size - 2, 6)  # Decrease by 2 points, but don't go below size 6
        current_font.setPointSize(new_font_size)
        self.text_edit.setFont(current_font)

    def on_mouse_move(self, event):
        """Highlight the textline under the mouse pointer and update the text bar."""
        if self.selected_textline:
            # If a textline is already selected, do not highlight others or update the text bar
            return
        
        mouse_x, mouse_y = event.x(), event.y()
        highlighted_textline = None

        for line in self.textlines:
            coordinates = line["coords"]  # List of points representing the contour
            path = QPainterPath()

            # Add the contour path (polygon)
            path.moveTo(coordinates[0][0], coordinates[0][1])
            for point in coordinates[1:]:
                path.lineTo(point[0], point[1])
            path.closeSubpath()  # Close the contour

            if path.contains(QPointF(mouse_x, mouse_y)):
                highlighted_textline = line
                break

        if highlighted_textline:
            self.text_bar.setText(f"{highlighted_textline['text']}")
            self.highlight_textline(mouse_x, mouse_y, persistent=None)  # Highlight textline
        else:
            self.text_bar.setText(" ")



            
    def return_textline_of_xml(self):
        tree1 = ET.parse(self.xml_path, parser = ET.XMLParser(encoding="utf-8"))
        root1=tree1.getroot()
        alltags=[elem.tag for elem in root1.iter()]
        link=alltags[0].split('}')[0]+'}'

        name_space = alltags[0].split('}')[0]
        name_space = name_space.split('{')[1]

        region_tags=np.unique([x for x in alltags if x.endswith('TextRegion')]) 
            

        self.textlines = []
        #tinl = time.time()
        indexer_text_region = 0
        indexer_textlines = 0
        for nn in root1.iter(region_tags):
            for child_textregion in nn:
                if child_textregion.tag.endswith("TextLine"):
                    id_textline = child_textregion.attrib['id']
                    for child_textlines in child_textregion:
                        if child_textlines.tag.endswith("Coords"):
                            #cropped_lines_region_indexer.append(indexer_text_region)
                            p_h=child_textlines.attrib['points'].split(' ')
                            textline_coords =  np.array( [ [ int(x.split(',')[0]) , int(x.split(',')[1]) ]  for x in p_h] )
                            
                            #print(textline_coords, 'textline_coords')
                            
                            

                        if child_textlines.tag.endswith("TextEquiv"):
                            for cheild_text in child_textlines:
                                if cheild_text.tag.endswith("Unicode"):
                                    textline_text = cheild_text.text
                                    if textline_text:
                                        dict_in ={}
                                        dict_in['coords'] = textline_coords
                                        dict_in['text'] = textline_text
                                        dict_in['id'] = id_textline
                                        #print(dict_in)
                                        self.textlines.append(dict_in)
                                        


    def highlight_textline(self, x, y, persistent=None):
        """Highlight only the textline under the mouse pointer or keep the selected textline highlighted."""
        self.highlighted_textline = None  # Reset highlighted textline

        # Draw the image and highlight the textline under the mouse
        if self.image_path.lower().endswith(('.tif', '.tiff')):
            painter_pixmap = QPixmap("temp_image.png")
        else:
            painter_pixmap = QPixmap(self.image_path)
        painter = QPainter(painter_pixmap)
        font = QFont("Arial", 12)
        painter.setFont(font)

        for line in self.textlines:
            coordinates = line["coords"]  # List of points representing the contour
            path = QPainterPath()

            # Add the contour path (polygon)
            path.moveTo(coordinates[0][0], coordinates[0][1])
            for point in coordinates[1:]:
                path.lineTo(point[0], point[1])
            path.closeSubpath()  # Close the contour

            if persistent and line["id"] == persistent["id"]:
                # If there's a persistent textline (e.g., the one being edited), keep it highlighted
                painter.setPen(QPen(Qt.green, 2))  # Highlight the persistent line in green
                painter.strokePath(path, QPen(Qt.green, 2))
                #painter.setPen(QPen(Qt.red, 2))
                #painter.drawText(coordinates[0][0] + 5, coordinates[0][1] - 5, line["text"])
            elif path.contains(QPointF(x, y)):
                # If the mouse is inside the contour, highlight it
                self.highlighted_textline = line
                painter.setPen(QPen(Qt.blue, 2))  # Highlight in blue
                painter.strokePath(path, QPen(Qt.blue, 2))
                #painter.setPen(QPen(Qt.red, 2))
                #painter.drawText(coordinates[0][0] + 5, coordinates[0][1] - 5, line["text"])

        painter.end()
        self.image_label.setPixmap(painter_pixmap)



    def on_mouse_press(self, event):
        """Enable editing for the clicked textline."""
        if self.highlighted_textline:
            self.selected_textline = self.highlighted_textline
            self.text_edit.setText(self.selected_textline["text"])
            self.text_edit.show()
            self.save_button.show()

    def save_text(self):
        """Save the edited text back to the selected textline."""
        if self.selected_textline:
            new_text = self.text_edit.text()
            self.selected_textline["text"] = new_text  # Update the textline's text
            self.text_edit.hide()
            self.save_button.hide()
            self.selected_textline = None  # Clear the persistent selection
            self.highlight_textline(-1, -1)  # Redraw the image to reflect updated text

                
                
    def save_all_textlines(self):
        """Save all textlines to a file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Textlines to File", "", "xml Files (*.xml);;All Files (*)"
        )
        if file_path:
            tree1 = ET.parse(self.xml_path, parser = ET.XMLParser(encoding="utf-8"))
            root1=tree1.getroot()
            alltags=[elem.tag for elem in root1.iter()]
            link=alltags[0].split('}')[0]+'}'

            name_space = alltags[0].split('}')[0]
            name_space = name_space.split('{')[1]

            region_tags=np.unique([x for x in alltags if x.endswith('TextRegion')]) 

            for nn in root1.iter(region_tags):
                for child_textregion in nn:
                    if child_textregion.tag.endswith("TextLine"):
                        id_textline = child_textregion.attrib['id']
                        for child_textlines in child_textregion:
                            if child_textlines.tag.endswith("TextEquiv"):
                                for cheild_text in child_textlines:
                                    if cheild_text.tag.endswith("Unicode"):
                                        try:
                                            text_corrected = [ind_dict['text'] for ind_dict in self.textlines if ind_dict['id']==id_textline][0]
                                            cheild_text.text = text_corrected
                                        except:
                                            pass
                                        
            ET.register_namespace("",name_space)
            tree1.write(file_path,xml_declaration=True,method='xml',encoding="utf8",default_namespace=None)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = TextlineEditorApp()
    window.show()
    sys.exit(app.exec())
