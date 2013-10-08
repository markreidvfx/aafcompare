import sys
import os
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.Qt import *

import time
import traceback

import aafcompare_backend
import aaf2xml

import save_xls

class Compare_Thread(QThread):
    
    def __init__(self,parent=None):
        super(Compare_Thread,self).__init__(parent)
        self.old_paths = None
        self.new_paths = None
        self.only_quicktimes =True
        self.aaf_dir = None
    
    def run(self):
        try:
            
            reload(aafcompare_backend)
            
            AAF  = aafcompare_backend.AAF_Compare(self.old_paths,self.new_paths)
            
            AAF.progress = self.progress
            AAF.progress_message = self.progress_message
            
            AAF.only_quicktimes = self.only_quicktimes
            
            AAF.base_dir = self.aaf_dir
            
            data = AAF.get_data()
            self.work_done(data)
            
        except:
            
            message = 'AFF Error\n'
            
            message += traceback.format_exc()
            self.work_error(message)
        
    def progress(self,value,max_value):
        
        self.emit(SIGNAL('progress'),value,max_value)
        
    def progress_message(self,message):
        self.emit(SIGNAL('progress_message'),message)
        
    def work_done(self,work):
        self.emit(SIGNAL('work_done'),work)
        
    def work_error(self,error):
        self.emit(SIGNAL('work_error'),error)

                  
            



class Dual_Listview_Widget(QWidget):
    def __init__(self,parent=None):
        super(Dual_Listview_Widget,self).__init__(parent)
        
        self.paths = {}
        
        self.current_old = None
        self.current_new = None
        
        self.base_dir = ""
        
        self.old = QListWidget()
        self.add_old = QPushButton("+")
        
        self.new = QListWidget()
        self.add_new = QPushButton("+")
        
        self.old.setSelectionMode(QAbstractItemView.ContiguousSelection)
        self.new.setSelectionMode(QAbstractItemView.ContiguousSelection)
        
        
        layout = QHBoxLayout()
        layout.setMargin(0)
        
        splitter = QSplitter()
        
        left = QWidget()
        right = QWidget()
        
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        
        left_layout.setMargin(0)
        right_layout.setMargin(0)
        
        left_layout.addWidget(QLabel('old'))
        left_layout.addWidget(self.add_old)
        left_layout.addWidget(self.old)
        
        right_layout.addWidget(QLabel('new'))
        right_layout.addWidget(self.add_new)
        right_layout.addWidget(self.new)
        
        left.setLayout(left_layout)
        right.setLayout(right_layout)
    
        
        splitter.addWidget(left)
        splitter.addWidget(right)
        
        layout.addWidget(splitter)
        
        self.setLayout(layout)
        self.connect(self.old,SIGNAL("currentItemChanged (QListWidgetItem *,QListWidgetItem *)"),self.old_changed)
        self.connect(self.new,SIGNAL("currentItemChanged (QListWidgetItem *,QListWidgetItem *)"),self.new_changed)
        
        self.connect(self.add_new, SIGNAL("clicked()"), self.pick_aaf)
        self.connect(self.add_old, SIGNAL("clicked()"), self.pick_aaf)
        
    def pick_aaf(self, new=False):
        
        files = QFileDialog.getOpenFileNames()
        
        if not files:
            return
        
        for item in files:
            self.addItem(str(item))
 
    def old_changed(self,item):
        try:
            path = self.paths[str(item.text())]
            
            self.current_old = path
    
            print 'old:',path
        except:
            pass
        
    def new_changed(self,item):
        try:
            path = self.paths[str(item.text())]
            
            self.current_new = path
            print 'new:',path
            
        except:
            pass
        
    def clear(self):
        self.old.clear()
        self.new.clear()
        
    def addItem(self,path):
        #basename = os.path.basename(path)
        
        
        #key = path.replace(self.base_dir + os.sep,'')
        key = path
        self.paths[key] = path
        
        self.old.addItem(key)
        self.new.addItem(key)
        
        if self.current_old == None:
            first_item = self.old.item(0)
            
            self.old.setCurrentItem(first_item)
            self.old_changed(first_item)
            
        if self.current_new == None:
            first_item = self.new.item(0)
            
            self.new.setCurrentItem(first_item)
            self.new_changed(first_item)
            
        
        
        pass
    def delItem(self,item):
        pass
    
    def get_selected(self):
        
        selected_old_items =self.old.selectedItems()
        selected_new_items = self.new.selectedItems()
        
        selected_old = []
        selected_new = []
        
        for item in selected_old_items:
            print item, self.paths
            path = self.paths[str(item.text())]
            
            selected_old.append(path)
            
        for item in selected_new_items:
            path = self.paths[str(item.text())]
            
            selected_new.append(path)
            
        return selected_old,selected_new
            
        



class Aff_Picker_Widget(QWidget):
    def __init__(self,parent=None):
        super(Aff_Picker_Widget,self).__init__(parent)
        
        self.listview = Dual_Listview_Widget()
        
        self.addButton = QPushButton('Add')
        self.delButton = QPushButton('Remove')
        self.refreshButton = QPushButton('Refresh')
        self.compareButton = QPushButton('Compare')
        self.only_quicktime_checkbox = QCheckBox('Only Quicktimes')
        
        self.only_quicktime_checkbox.setChecked(True)
        
        
        buttonLayout = QVBoxLayout()
        buttonLayout.setMargin(0)
        #buttonLayout.addWidget(self.addButton)
        #buttonLayout.addWidget(self.delButton)
        buttonLayout.addWidget(self.refreshButton)
        buttonLayout.addWidget(self.compareButton)
        buttonLayout.addWidget(self.only_quicktime_checkbox)
        
        
        buttonWidget = QWidget()
        buttonWidget.setLayout(buttonLayout)
        
        layout= QHBoxLayout()
        layout.addWidget(self.listview)
        layout.addWidget(buttonWidget)
        
        self.setLayout(layout)
        self.dirpath = None
        
        #dirpath = os.path.dirname(os.path.abspath(__file__))
        
        #aaf_path = os.path.join(dirpath,'test')
        
        #self.addDir(aaf_path)
        
        self.connect(self.compareButton,SIGNAL('clicked()'),self.compare)
        self.connect(self.refreshButton,SIGNAL('clicked()'),self.refresh)
        
        
    def get_selected(self):
        return self.listview.get_selected()
        
    def refresh(self):
        self.listview.clear()
        self.setDir(self.dirpath)
        
    def only_quicktimes(self):
        return self.only_quicktime_checkbox.isChecked()
        
    def compare(self):
        current_old = self.listview.current_old
        current_new = self.listview.current_new
        #print current_info,current_compare
        
        
        self.emit(SIGNAL("compare"), current_old,current_new)
        
    def setDir(self,path):
        
        self.listview.base_dir = path
        self.dirpath  = path
        
        aaf_files = []
        for root,dirs,files, in os.walk(path):
            
            
            for item in files:
                
                name,ext = os.path.splitext(item)
                
                full_path = os.path.join(root,item)
                
                if ext.lower() == '.aaf':
                    aaf_files.append(full_path)
                    #self.listview.addItem(full_path)

        for item in sorted(aaf_files):
            self.listview.addItem(item)
        
        #self.pass
class Progress_Widget(QWidget):
    def __init__(self,parent=None):
        super(Progress_Widget,self).__init__(parent)
        
        self.progress = QProgressBar()
        
        self.progress_message = QLabel()
        
        layout = QHBoxLayout()
        
        layout.addWidget(self.progress)
        layout.addWidget(self.progress_message)
        
        self.setLayout(layout)
        
        self.progress.setMinimum(0)
        self.progress.setMaximum(0)
        
        self.set_message('Reading AAF files')
        
        
    def set_progress(self,value,value_max):
        self.progress.setMaximum(value_max)
        self.progress.setValue(value)
        
    def set_message(self,message):
        self.progress_message.setText(message)
        
    
class ChangeList_Manager_Widget(QWidget):
    def __init__(self,aaf_dir=None,parent=None):
        super(ChangeList_Manager_Widget,self).__init__(parent)
        
        self.picker = Aff_Picker_Widget()
        self.info = Aff_Info_Widget()
        
        self.old_path = None
        self.new_path = None
        
        self.aaf_dir = aaf_dir
        
        self.xls_button = QPushButton('Save XLS')
        
        self.xls_button.setEnabled(False)
        
        self.progress = Progress_Widget()
        self.progress.hide()
        
        
        self.compare_thread = Compare_Thread()
        
        layout = QVBoxLayout()
        
        splitter =QSplitter()
        
        topWidget = QWidget()
        topWidget_layout = QVBoxLayout()
        topWidget_layout.setMargin(0)
        topWidget_layout.addWidget(self.picker)
        topWidget_layout.addWidget(self.progress)
        
        topWidget.setLayout(topWidget_layout)
        
        splitter.addWidget(topWidget)
        splitter.setOrientation(Qt.Vertical)
        
        bottomWidget = QWidget()
        bottomWidget_layout = QVBoxLayout()
        bottomWidget_layout.setMargin(0)
        bottomWidget_layout.addWidget(self.info)
        bottomWidget_layout.addWidget(self.xls_button)
        
        bottomWidget.setLayout(bottomWidget_layout)
        
        splitter.addWidget(topWidget)
        splitter.addWidget(bottomWidget)
        
        layout.addWidget(splitter)
        
        self.setLayout(layout)
        
        self.connect(self.picker,SIGNAL("compare"),self.Start_Compare)
        self.connect(self.xls_button,SIGNAL('clicked()'),self.save_xls)
        
        
        
        self.connect(self.compare_thread,SIGNAL("work_done"),self.Load_Compare)
        self.connect(self.compare_thread,SIGNAL("work_error"),self.Load_Error)
        
        self.connect(self.compare_thread,SIGNAL("progress"),self.progress.set_progress)
        self.connect(self.compare_thread,SIGNAL("progress_message"),self.progress.set_message)
        
        if aaf_dir:
            self.picker.setDir(os.path.join(aaf_dir,'AAF'))
        
        
    def Start_Compare(self,old,new):
        
        #print info
        #print compare
        
        print '**',old
        print '**',new
        
        self.old_path = new
        self.new_path = old
        
        selected_old,selected_new = self.picker.get_selected()
        
        print selected_old
        print selected_new
        
        #raise Exception()
        
        self.only_quicktimes = self.picker.only_quicktimes()
        
        self.compare_thread.old_paths = selected_old
        self.compare_thread.new_paths = selected_new
        
        
        self.compare_thread.aaf_dir = self.aaf_dir
        
        self.compare_thread.only_quicktimes = self.picker.only_quicktimes()
        
        
        self.picker.setDisabled(True)
        self.progress.show()
        
        self.compare_thread.start()
        
    def Load_Compare(self,data):
        
        #print data
        
        self.data = data
        
        self.picker.setDisabled(False)
        self.progress.hide()
        
        self.info.loadData(data)
        self.xls_button.setEnabled(True)
        
    def Load_Error(self,error):
        self.picker.setDisabled(False)
        self.progress.hide()
        QMessageBox.critical(self,'Error',error)
        
    def save_xls(self):
        
        xls_path  = QFileDialog.getSaveFileName(filter="XLS files (*.xls)")
        
        if not xls_path:
            return
        
        reload(save_xls)
        
        try:
            save_xls.save_xls(self.data,xls_path)
            
        except:
            self.Load_Error(traceback.format_exc())
            
            return
        
        
#launch_filebrowser(xls_path)
   
            
        
        
class Clip_Tree_Widget(QWidget):
    
    def __init__(self,parent=None):
        super(Clip_Tree_Widget,self).__init__(parent)
        
        self.collapse_expand_button = QPushButton('Expand/Collapse')
        self.expanded = True
        
        self.headers = []
        
        self.view = QTreeWidget()
        self.view.setAlternatingRowColors(True)
        
        self.totals = QLabel()
        
        toolbar_layout = QHBoxLayout()
        toolbar_layout.addWidget(self.collapse_expand_button)
        
        layout = QVBoxLayout()
        layout.setMargin(0)
        
        layout.addLayout(toolbar_layout)
        layout.addWidget(self.view)
        layout.addWidget(self.totals)
        
        self.connect(self.collapse_expand_button,SIGNAL('clicked()'),self.toggle_expand)
        
        self.connect(self.view,SIGNAL('itemExpanded (QTreeWidgetItem *)'),self.auto_resizeColumns)
        
        self.setLayout(layout)
        
    def toggle_expand(self):
        
        if self.expanded:
            self.view.collapseAll()
            self.expanded = False
            self.auto_resizeColumns()
            
        else:
            self.expanded = True
            self.view.expandAll()
            self.auto_resizeColumns()
            
                
    def auto_resizeColumns(self,*args):
        for i,item in enumerate(self.headers):
        
            self.view.resizeColumnToContents(i)
        
        
        
    def set_totals(self,totals):
        total_strings = []
        for item in totals:
            item_name = item[0]
            item_value = item[1]
            
            total_strings.append( '(%s) %s' % (item_value,item_name))
            
        self.totals.setText(', '.join(total_strings))
        
        
    def make_treeItem(self,data,headers):
        #print data
        
        treeItem = QTreeWidgetItem()
        
        
        status = None
        
        for i,item in enumerate(headers):
            
            if data.has_key(item):
                treeItem.setText(i,str(data[item]))
                
                if item == 'status':
                    status  = data[item]
                
        if status:
            for i,item in enumerate(headers):
            
                if data.has_key(item):
                    if status == 'Missing':
                        treeItem.setTextColor(i,QColor(255,0,0,255))
                        
                    elif status == 'New':
                        treeItem.setTextColor(i,QColor(0,150,0,255))
                        
                    elif status == 'Modified':
                        
                        treeItem.setTextColor(i,QColor(0,0,150,255))
                        
                    elif status == 'Shifted':
                        treeItem.setTextColor(i,QColor(150,0,150,255))
            
        
                                    
        if data.has_key('children'):
            for item in data['children']:
                child = self.make_treeItem(item,headers)
                
                treeItem.addChild(child)
                
        return treeItem
                
    
        
        
    def loadData(self,data):
        
        self.clear()
        
        info = data[0]
        
        
        headers = info['headers']
        totals = info['totals']
        
        self.set_totals(totals)
        
        self.view.setSortingEnabled(False)
        
        capHeaders = []
        for i,item in enumerate(headers):
            capHeaders.append(item.capitalize())
        
        self.view.setHeaderLabels(capHeaders)
        
        
        
        for item in data[1:]:
            
            treeItem=self.make_treeItem(item,headers)
            
            self.view.addTopLevelItem(treeItem)
            
            
            
        self.view.setSortingEnabled(True)
        
        self.view.sortByColumn(0,Qt.AscendingOrder)
        
        if self.expanded:
            self.view.expandAll()
            self.expanded = True
        
        for i,item in enumerate(headers):
        
            self.view.resizeColumnToContents(i)
        
        self.headers = headers
            
    
    def clear(self):
        self.view.clear()
        
        
        
        
class Aff_Info_Widget(QWidget):
    def __init__(self,parent=None):
        super(Aff_Info_Widget,self).__init__(parent)
        self.data = None
        
        self.info_title = QLabel("Compare Info:")
        self.tabview = QTabWidget()
        
        self.summarry = Clip_Tree_Widget()
        self.missing = Clip_Tree_Widget()
        self.new = Clip_Tree_Widget()
        self.shifted = Clip_Tree_Widget()
        self.modified = Clip_Tree_Widget()
        self.original = Clip_Tree_Widget()
        
        self.editorial = Clip_Tree_Widget()
        self.ds_online = Clip_Tree_Widget()
        
        self.other = QTextBrowser()
        
        self.new_shot_totals = QTextBrowser()
        self.old_shot_totals = QTextBrowser()
        
        self.new_vfx_counts = QTextBrowser()
        self.old_vfx_counts = QTextBrowser()
        
        self.tabview.addTab(self.summarry,'Summary')
        self.tabview.addTab(self.missing,'Missing')
        self.tabview.addTab(self.new,'New')
        self.tabview.addTab(self.shifted,'Shifted')
        self.tabview.addTab(self.modified,'Modified')
        self.tabview.addTab(self.original,'Original')
        
        self.tabview.addTab(self.editorial,'Editorial')
        self.tabview.addTab(self.ds_online,'DS Online')
        
        self.tabview.addTab(self.old_shot_totals,'Old Shot Totals')
        self.tabview.addTab(self.new_shot_totals,'New Shot Totals')
        
        self.tabview.addTab(self.old_vfx_counts,"Old VFX Counts")
        self.tabview.addTab(self.new_vfx_counts,"New VFX Counts")
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_title)
        layout.addWidget(self.tabview)
        
        self.setLayout(layout)
        
    def clear(self):
        self.summarry.clear()
        
    def loadData(self,data):
        self.clear()
        
        self.summarry.loadData(data['summary'])
        self.missing.loadData(data['missing'])
        self.new.loadData(data['new'])
        
        self.shifted.loadData(data['shifted'])
        self.modified.loadData(data['modified'])
        self.original.loadData(data['original'])
        
        self.editorial.loadData(data['Editorial'])
        self.ds_online.loadData(data['DS Online'])
        
        
        old_shot_totals = data['old_shot_totals']
        new_shot_totals = data['new_shot_totals']
        #self.other.clear()
        #self.other.append(other_data)
        
        self.old_shot_totals.clear()
        self.new_shot_totals.clear()
        
        self.old_shot_totals.append(old_shot_totals)
        self.new_shot_totals.append(new_shot_totals)
        
        self.new_vfx_counts.clear()
        self.old_vfx_counts.clear()
        
        old_vfx_counts = data['old_vfx_counts']
        new_vfx_counts = data['new_vfx_counts']
        
        self.old_vfx_counts.append(old_vfx_counts)
        self.new_vfx_counts.append(new_vfx_counts)
        
        old,new = data['aaf_names']
        
        self.info_title.setText('Compare Info:  %s --> %s' % ( old,new))
        #print data
        #self.data = data
        
        
        pass
            
        
        
def run_gui(aaf_dir=None):
    
    if not aaf_dir:
        aaf_dir = os.path.dirname(__file__)
    app = QApplication(sys.argv)
    main = ChangeList_Manager_Widget(aaf_dir)
    main.setWindowTitle("ChangeList Manager")
    main.show()
    main.raise_()
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    test_aaf_dir = os.path.join(os.path.dirname(__file__),'changelist_manager')
    #if not os.path.exists(test_aaf_dir):
    #os.makedirs(test_aaf_dir)
    run_gui(test_aaf_dir)
