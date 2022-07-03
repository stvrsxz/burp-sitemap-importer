from burp import IBurpExtender, ITab, IHttpRequestResponse, IHttpService

from java.awt import Dimension
from javax.swing import (
    JFileChooser,
    JButton,
    JPanel,
    BoxLayout,
    JComponent,
    Box,
    JProgressBar,
    SwingWorker,
)
from javax.swing.JOptionPane import showMessageDialog, INFORMATION_MESSAGE

from xml.sax import parse
from xml.sax.handler import ContentHandler


class BurpExtender(IBurpExtender, ITab):
    def registerExtenderCallbacks(self, callbacks):
        self.callbacks = callbacks
        self.helpers = callbacks.getHelpers()

        callbacks.setExtensionName("Sitemap Importer")
        callbacks.addSuiteTab(self)

        self.items_added = 0

    def getTabCaption(self):
        return "Import Sitemap"

    def getUiComponent(self):
        self.panel = JPanel()
        self.panel.layout = BoxLayout(self.panel, BoxLayout.Y_AXIS)

        self.panel.add(Box.createRigidArea(Dimension(50, 50)))

        self.button = JButton(
            "Import Sitemap XML files", actionPerformed=self.import_sitemaps
        )
        self.button.setAlignmentX(JComponent.CENTER_ALIGNMENT)
        self.panel.add(self.button)

        self.panel.add(Box.createRigidArea(Dimension(50, 50)))

        self.progress_bar = JProgressBar()
        self.progress_bar.setIndeterminate(True)
        self.progress_bar.setMaximumSize(Dimension(200, 10))
        self.progress_bar.setVisible(False)
        self.panel.add(self.progress_bar)

        self.callbacks.customizeUiComponent(self.panel)

        return self.panel

    def import_sitemaps(self, event):
        self.button.setEnabled(False)

        filechooser = JFileChooser()
        filechooser.setDialogTitle("Select Sitemap XML files")
        filechooser.setFileSelectionMode(JFileChooser.FILES_ONLY)
        filechooser.setMultiSelectionEnabled(True)

        selected = filechooser.showOpenDialog(self.panel)
        if selected == JFileChooser.APPROVE_OPTION:
            selected_files = filechooser.getSelectedFiles()

            # Parse files and add their items to the site map in the background
            worker = ParseToSiteMapWorker(self, selected_files)
            worker.execute()

        else:
            self.button.setEnabled(True)

    def parse_and_add_to_sitemap(self, selected_files):
        self.progress_bar.setVisible(True)

        print "Opening: %s files" % len(selected_files)
        for selected_file in selected_files:
            with open(selected_file.getAbsolutePath(), "r") as file_:
                sitemap_handler = SiteMapHandler(
                    self
                )  # We need to use the burp extender object inside the handler object
                parse(file_, sitemap_handler)

        self.progress_bar.setVisible(False)
        self.log_result()

        self.items_added = 0  # reset the main item counter

        self.button.setEnabled(True)

    def log_result(self):
        added_items_message = "Added %s items to sitemap" % self.items_added

        print added_items_message
        self.callbacks.issueAlert(added_items_message)
        showMessageDialog(
            self.panel, added_items_message, "Sitemap Imported", INFORMATION_MESSAGE
        )


class SiteMapHandler(ContentHandler):
    def __init__(self, burp_extender):
        self.burp_extender = burp_extender
        self.item = {}  # the sitemap item
        self.current_element_data = None

    def characters(self, data):
        self.current_element_data = data

    def endElement(self, name):
        if name == "item":
            item = HttpRequestResponse(
                request=self.burp_extender.helpers.base64Decode(
                    self.item.get("request")
                ),
                response=self.burp_extender.helpers.base64Decode(
                    self.item.get("response")
                ),
                http_service=HttpService(
                    self.item.get("host"),
                    self.item.get("port"),
                    self.item.get("protocol"),
                ),
                color=self.item.get("color"),
                comment=self.item.get("comment"),
            )

            self.burp_extender.callbacks.addToSiteMap(item)
            self.burp_extender.items_added += 1

            # Reset the stored buffers after every item
            self.item = {}
            self.current_element_data = None
        else:
            self.item[name] = self.current_element_data


class HttpRequestResponse(IHttpRequestResponse):
    def __init__(self, request, response, http_service, color=None, comment=None):
        self._request = request
        self._response = response
        self._http_service = http_service
        self._color = color
        self._comment = comment

    def getRequest(self):
        return self._request

    def getResponse(self):
        return self._response

    def getHttpService(self):
        return self._http_service

    def getComment(self):
        return self._color

    def getHighlight(self):
        return self._comment


class HttpService(IHttpService):
    def __init__(self, host, port, protocol):
        self._host = host
        self._port = port
        self._protocol = protocol

    def getHost(self):
        return self._host

    def getPort(self):
        return int(self._port)

    def getProtocol(self):
        return self._protocol


class ParseToSiteMapWorker(SwingWorker):
    def __init__(self, extender, selected_files):
        self.extender = extender
        self.selected_files = selected_files

    def doInBackground(self):
        self.extender.parse_and_add_to_sitemap(self.selected_files)
        return
