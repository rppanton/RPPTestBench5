
import os, sys, shutil
import resources
from git import Repo

from PyQt5.QtWidgets import QApplication, QWidget, QComboBox, QLabel, QHeaderView, QFileDialog, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QTableWidgetItem
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt
from PyQt5.uic import loadUi

class GitUpdater(QMainWindow):
	def __init__(self, parent = None):
		super(GitUpdater, self).__init__(parent)
		loadUi("gitUpdater.ui", self)
		self.setWindowIcon(QIcon(":/git/git-for-windows.ico"))
		
		self.repo = None
		self.indx = None
		
		self.comms.setColumnCount(3)
		header = self.comms.horizontalHeader()
		header.setSectionResizeMode(QHeaderView.ResizeToContents)
		header.setSectionResizeMode(1, QHeaderView.Stretch)
		self.comms.setHorizontalHeaderItem(0, QTableWidgetItem("Hash code"))
		self.comms.setHorizontalHeaderItem(1, QTableWidgetItem("Head"))
		self.comms.setHorizontalHeaderItem(2, QTableWidgetItem("Commit date"))
		
		self.btn_path.clicked.connect(self.dir_dialog)
		self.btn_pull.clicked.connect(self.pull_repo)
		self.comms.cellPressed.connect(self.com_select)
		
		local = os.path.abspath(".git")
		
		if os.path.exists(local):
			self.local_path.setText(local)
		else:
			self.dir_dialog()

		self.repo = Repo(self.local_path.text())
		for remote in self.repo.remotes:
			rem = self.r_path.text() + remote.url
			self.r_path.setText(rem)
		if not self.repo.bare:
			print "Local active branch: {}".format(self.repo.active_branch)
			commits = list(self.repo.heads)
			for c in commits:
				c_list = list(self.repo.iter_commits(c))
				for commit in c_list:
				# commit = c_list[0]
					n = self.comms.rowCount()
					self.comms.insertRow(n)
					self.comms.setRowHeight(n, 25)
					self.comms.setItem(n, 0, QTableWidgetItem(str(commit.hexsha[:8])))
					self.comms.setItem(n, 1, QTableWidgetItem(str(commit.summary)))
					# self.comms.setItem(n, 1, QTableWidgetItem(str(c)))
					self.comms.setItem(n, 2, QTableWidgetItem(str(commit.authored_datetime)))
		else:
			print('Could not load repository at {} :('.format(repo_path))

	def dir_dialog(self):
		self.outdir = None
		dirName = QFileDialog.getExistingDirectory(self, "Select a local Git repository", "..\TestBench5\.git", QFileDialog.ShowDirsOnly)
		self.outdir = dirName
		if self.outdir:
			self.local_path.setText(self.outdir)
		else:
			print "Local Git repository not chosed"
			return

	def com_select(self, row, column):
		self.differs.clear()
		id = self.comms.item(row, 0).text()
		self.indx = row
		hcommit = self.repo.commit(id)
		for f in hcommit.diff(None):
			self.differs.append(str(f)+"\n")
		self.btn_pull.setEnabled(True)
		
	def pull_repo(self):
		if self.rb_override.isChecked():
			print " * Deleting old files and dirs..."
			p = self.local_path.text().replace("\.git", "")
			print "From", p
			
			all = os.listdir(p)
			if ".git" in all:
				all.remove(".git")
			if "configuration.xml" in all:
				all.remove("configuration.xml")
			for the_file in all:
				file_path = os.path.join(p, the_file)
				try:
					if os.path.isfile(file_path):
						os.unlink(file_path)
					elif os.path.isdir(file_path):
						shutil.rmtree(file_path)
				except Exception as e:
					print(e)
			
		print " * Pulling files from the Git..."
		self.repo.config_writer()
		print "Pulling from: {}".format(self.repo.heads[self.indx])
		head = self.repo.heads[self.indx]
		head.checkout(force=True)
		remo = self.repo.remote()
		try:
			remo.pull(head)
		except Exception, ex:
			print "Pull exception: {}".format(ex)
			pass
		finally:
			print "Synchronization is done"
			self.repo.close()

if __name__ == '__main__':
	app = QApplication(sys.argv)
	gu = GitUpdater()
	gu.show()
	sys.exit(app.exec_())