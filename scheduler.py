import argparse, os, logging, ntpath
import xml.etree.ElementTree as ET
# from xml.dom import minidom
from xml.sax.handler import ContentHandler
from xml.sax import make_parser
from lxml import etree


class Node:
    def __init__(self, value):
        self.value = value
        self.reference = None

    def getData(self):
        return self.value

    def getNext(self):
        return self.reference

    def setData(self, newvalue):
        self.value = newvalue

    def setNext(self, newref):
        self.reference = newref


class LinkedList:
    def __init__(self):
        self.head = None

    def __iter__(self):
        current = self.head
        while True:
            if current.reference is not None:
                current = current.reference
                yield current.value
            else:
                raise StopIteration

    def __contains__(self, item):
        current = self.head
        while current is not None:
            if current.value == item:
                return True
            current = current.reference
        return False

    def isEmpty(self):
        return self.head is None

    def add(self, newvalue): # add nodes at the end
        if self.head is None:
            self.head = Node(newvalue)
        else:
            current = self.head
            while current.reference is not None:
                current = current.reference
            current.reference = Node(newvalue)


    def insert_before(self, item, element):  # insert item before element
        current = self.head
        counter = 0
        temp = Node(item)
        prev = None
        if current is None:
            temp.setNext(self.head)
            self.head = temp
        else:
            while current.getData() != element:
                prev = current
                current = current.getNext()
                counter = counter + 1
            temp.setNext(prev.getNext())
            prev.setNext(temp)
            current.setData = temp

    def insert_after(self, item, element):  # insert item after element
        current = self.head
        counter = 0
        temp = Node(item)
        if current is None:
            temp.setNext(self.head)
            self.head = temp
        else:
            while current.getData() != element:
                current = current.getNext()
                counter = counter + 1
            temp.setNext(current.getNext())
            current.setNext(temp)
            current.setData = temp

    def length(self):
        temp = self.head
        count = 0
        while temp:
            count += 1
            temp = temp.reference
        return count

    def count(self, value):
        count_sum = 0
        for item in self:
            if item == value:
                count_sum += 1
        return count_sum

    def remove_node(self, value):
        prev = None
        current = self.head
        while current:
            if current.getData == value:
                if prev:
                    prev.setNext(current.getNext())
                else:
                    self.head = current.getNext()
                return True
            prev = current
            current = current.getNext()
        return False


def main():
    # parsing the command line arguments
    parser = argparse.ArgumentParser()
    arg_parse(parser)
    args = parser.parse_args()
    input_directory = args.input_directory
    output_directory = args.output_path
    # setting input and output paths
    input_path = input_directory.replace("\\", "/")
    output_path = output_directory.replace("\\", "/")
    # logger creation and setting
    logger = logging.getLogger('result')
    hdlr = logging.FileHandler(output_path + '/result.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.INFO)
    open(output_path + '/result.log', 'w').close()

    #retrieve_data(input_path, logger)
    create_list(input_path, output_path, logger)


def arg_parse(parser):
    # adding command line options
    parser.add_argument("input", help="specify the input parameters")
    parser.add_argument("input_directory", help="location of input files")
    parser.add_argument("output", help="specify the output parameters")
    parser.add_argument("output_path", help="folder which will contain the output files")


def retrieve_data(input_path, logger):
    current_path = os.path.realpath(__file__)
    head, tail = ntpath.split(current_path)
    xsd_path = head + '/AUTOSAR_4-2-2_STRICT.xsd'
    path = xsd_path.replace("\\", "/")
    events = []
    events_additional = []
    swc_allocation = []
    for directory, directories, files in os.walk(input_path):
        for file in files:
            if file.endswith('arxml'):
                fullname = os.path.join(directory, file)
                try:
                    check_if_xml_is_wellformed(fullname)
                    logger.info('The file: ' + fullname + ' is well-formed')
                except Exception as e:
                    logger.error('The file: ' + fullname + ' is not well-formed: ' + str(e))
                    return
                validate_xml_with_xsd(path, fullname, logger)
                tree = etree.parse(fullname)
                root = tree.getroot()
                evt_event = root.findall(".//{http://autosar.org/schema/r4.0}DATA-RECEIVED-EVENT")
                per_event = root.findall(".//{http://autosar.org/schema/r4.0}TIMING-EVENT")
                for elem in evt_event:
                    obj_event = {}
                    obj_event['NAME'] = elem.find('{http://autosar.org/schema/r4.0}SHORT-NAME').text
                    obj_event['TYPE'] = "EVT"
                    obj_event['DURATION'] = "1µs"
                    obj_event['BEFORE-EVENT'] = ""
                    obj_event['AFTER-EVENT'] = ""
                    obj_event['CORE'] = ""
                    obj_event['ASIL'] = ""
                    if elem.find('{http://autosar.org/schema/r4.0}PERIOD') is not None:
                        obj_event['PERIOD'] = elem.find('{http://autosar.org/schema/r4.0}PERIOD').text
                    obj_event['ASWC'] = elem.getparent().getparent().getparent().getparent().getchildren()[0].text
                    events.append(obj_event)
                for elem in per_event:
                    obj_event = {}
                    obj_event['NAME'] = elem.find('{http://autosar.org/schema/r4.0}SHORT-NAME').text
                    obj_event['TYPE'] = "PER"
                    obj_event['DURATION'] = ""
                    obj_event['BEFORE-EVENT'] = ""
                    obj_event['AFTER-EVENT'] = ""
                    obj_event['CORE'] = ""
                    obj_event['ASIL'] = ""
                    if elem.find('{http://autosar.org/schema/r4.0}PERIOD') is not None:
                        obj_event['PERIOD'] = elem.find('{http://autosar.org/schema/r4.0}PERIOD').text
                    obj_event['ASWC'] = elem.getparent().getparent().getparent().getparent().getchildren()[0].text
                    events.append(obj_event)
            elif file.endswith('xml'):
                fullname = os.path.join(directory, file)
                try:
                    check_if_xml_is_wellformed(fullname)
                    logger.info('The file: ' + fullname + ' is well-formed')
                except Exception as e:
                    logger.error('The file: ' + fullname + ' is not well-formed: ' + str(e))
                    return
                validate_xml_with_xsd(path, fullname, logger)
                tree = etree.parse(fullname)
                root = tree.getroot()
                event = root.findall(".//EVENT")
                swc = root.findall(".//SWC-ALLOCATION")
                for element in event:
                    obj_event = {}
                    obj_event['EVENT'] = element.find('EVENT-REF').text
                    if element.find('DURATION') is not None:
                        obj_event['DURATION'] = element.find('DURATION').text
                    else:
                        obj_event['DURATION'] = "1µs"
                    if element.find('AFTER-EVENT-REF') is not None:
                        obj_event['AFTER-EVENT'] = element.find('AFTER-EVENT-REF').text
                    else:
                        obj_event['AFTER-EVENT'] = ""
                    if element.find('BEFORE-EVENT-REF') is not None:
                        obj_event['BEFORE-EVENT'] = element.find('BEFORE-EVENT-REF').text
                    else:
                        obj_event['BEFORE-EVENT'] = ""
                    events_additional.append(obj_event)
                for element in swc:
                    obj_event = {}
                    obj_event['SWC'] = element.find('SWC-REF').text
                    obj_event['CORE'] = element.find('CORE').text
                    obj_event['ASIL'] = element.find('ASIL').text
                    swc_allocation.append(obj_event)
    for index_event in range(len(events)):
        for index_info in range(len(events_additional)):
            if events[index_event]['NAME'] == events_additional[index_info]['EVENT']:
                events[index_event]['BEFORE-EVENT'] = events_additional[index_info]['BEFORE-EVENT']
                events[index_event]['AFTER-EVENT'] = events_additional[index_info]['AFTER-EVENT']
                events[index_event]['DURATION'] = events_additional[index_info]['DURATION']
    for index_event in range(len(events)):
        for index_aswc in range(len(events_additional)):
            if events[index_event]['ASWC'] == swc_allocation[index_aswc]['SWC']:
                events[index_event]['CORE'] = swc_allocation[index_aswc]['CORE']
                events[index_event]['ASIL'] = swc_allocation[index_aswc]['ASIL']
    for elem in events:
        print(elem)
    event_list = LinkedList()
    for elem in events:
        added = False
        if elem['AFTER-EVENT'] != "":
            if elem['AFTER-EVENT'] in event_list:
                event_list.insert_after(elem['NAME'], elem['AFTER-EVENT'])
            else:
                # print("cannot create dependence AFTER: " + elem['AFTER-EVENT'] + ": not present for " + elem['NAME'])
                event_list.add(elem['AFTER-EVENT'])
                event_list.add(elem['NAME'])
                added = True
        if elem['BEFORE-EVENT'] != "":
            if elem['BEFORE-EVENT'] in event_list:
                event_list.insert_before(elem['NAME'], elem['BEFORE-EVENT'])
            elif added is False:
                # print("cannot create dependence BEFORE:" + elem['BEFORE-EVENT'] + ": not present for " + elem['NAME'])
                event_list.add(elem['NAME'])
                event_list.add(elem['BEFORE-EVENT'])
                added = True
            else:
                print("cannot create dependence BEFORE: " + elem['BEFORE-EVENT'] + ": not present for " + elem['NAME'])
                added = True
        if added is False:
            if elem['AFTER-EVENT'] == "" and elem['BEFORE-EVENT'] == "":
                if elem['NAME'] not in event_list:
                    event_list.add(elem['NAME'])
    current = event_list.head
    while current is not None:
        print(current, current.value)
        current = current.reference
    current = event_list.head
    for i in range(event_list.length()):
        if event_list.count(current.value) > 1:
            print("cycle identified")
            break
        current = current.reference



def create_list(input_path, output_path, logger):
    current_path = os.path.realpath(__file__)
    head, tail = ntpath.split(current_path)
    xsd_path = head + '/AUTOSAR_4-2-2_STRICT.xsd'
    path = xsd_path.replace("\\", "/")
    events = []
    for directory, directories, files in os.walk(input_path):
        for file in files:
            if file.endswith('xml'):
                fullname = os.path.join(directory, file)
                try:
                    check_if_xml_is_wellformed(fullname)
                    logger.info('The file: ' + fullname + ' is well-formed')
                except Exception as e:
                    logger.error('The file: ' + fullname + ' is not well-formed: ' + str(e))
                    return
                validate_xml_with_xsd(path, fullname, logger)
                tree = etree.parse(fullname)
                root = tree.getroot()
                event = root.findall(".//EVENT")
                for element in event:
                    obj_event = {}
                    after_list = []
                    before_list = []
                    duration = "1µs"
                    for child in element.iterchildren():
                        if child.tag == 'EVENT-REF':
                            obj_event['EVENT'] = child.text
                        if child.tag == 'DURATION':
                            duration = child.text
                        if child.tag == 'AFTER-EVENT-REF':
                            after_list.append(child.text)
                        if child.tag == 'BEFORE-EVENT-REF':
                            before_list.append(child.text)
                    obj_event['DURATION'] = duration
                    obj_event['AFTER-EVENT'] = after_list
                    obj_event['BEFORE-EVENT'] = before_list
                    events.append(obj_event)
    priority = []
    for elem in events:
        task = elem['EVENT']
        count = 0
        structure = {}
        for element in events:
            if task in element['AFTER-EVENT']:
                count = count + 1
            if task in element['BEFORE-EVENT']:
                count = count - 1
        structure['EVENT'] = task
        structure['PRIORITY'] = count
        if elem['DURATION'] is not None:
            structure['DURATION'] = elem['DURATION']
        if elem['AFTER-EVENT'] is not None:
            structure['AFTER-EVENT'] = elem['AFTER-EVENT']
        if elem['BEFORE-EVENT'] is not None:
            structure['BEFORE-EVENT'] = elem['BEFORE-EVENT']
        priority.append(structure)
    sorted_list = sorted(priority, key=lambda k: k['PRIORITY'], reverse=True)
    event_list = LinkedList()
    for elem in sorted_list:
        event_list.add(elem)
    current = event_list.head
    while current is not None:
        print(current, current.value)
        current = current.reference
    for elem in event_list:
        temp = elem['BEFORE-EVENT']
        if temp:
            event_list.remove_node(elem)
            event_list.insert_before(elem, elem['BEFORE-EVENT'])
    current = event_list.head
    while current is not None:
        print(current, current.value)
        current = current.reference



def validate_xml_with_xsd(path_xsd, path_xml, logger):
    # load xsd file
    xmlschema_xsd = etree.parse(path_xsd)
    xmlschema = etree.XMLSchema(xmlschema_xsd)
    # validate xml file
    xmldoc = etree.parse(path_xml)
    if xmlschema.validate(xmldoc) is not True:
        logger.warning('The file: ' + path_xml + ' is NOT valid with the AUTOSAR4.2.2-STRICT  schema')
    else:
        logger.info('The file: ' + path_xml + ' is valid with the AUTOSAR4.2.2-STRICT schema')


def check_if_xml_is_wellformed(file):
    parser = make_parser()
    parser.setContentHandler(ContentHandler())
    parser.parse(file)


if __name__ == "__main__":
        main()
