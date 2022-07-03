# Burp sitemap importer

A simple (and experimental) burp extension, written in Jython, for importing burp sitemap XML files.

### Installation:

1. Clone this repo or download the `sitemap_importer.py` file.
2. Download the jython standalone jar from [here](https://www.jython.org/download.html).
3. Go to `Burp`:
    - `Extender`:
        - `Options`:
            - Add the downloaded jar to the `Location of Jython standalone JAR file`
        - `Extensions`:
            - `Add`:
                - Select `Python` in the `Extension type`
                - `Select file:` and add the `sitemap_importer.py`
         