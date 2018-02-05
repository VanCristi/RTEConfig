import argparse, os, logging, ntpath
from collections import defaultdict
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
            if current.getData() == value:
                if prev:
                    prev.setNext(current.getNext())
                else:
                    self.head = current.getNext()
                return True
            prev = current
            current = current.getNext()
        return False

    def find_node(self, value):
        current = self.head
        while current:
            item = current.getData()
            temp = item['EVENT']
            if item['EVENT'] in value:
                return item
            current = current.getNext()
        return False


# https://www.geeksforgeeks.org/topological-sorting/
# https://www.geeksforgeeks.org/detect-cycle-in-a-graph/
class Graph:
    def __init__(self, vertices):
        self.graph = defaultdict(list)  # dictionary containing adjacency List
        self.V = vertices  # No. of vertices

    # function to add an edge to graph
    def add_edge(self, u, v):
        self.graph[u].append(v)

    # A recursive function used by topologicalSort
    def topological_sort_util(self, v, visited, stack):

        # Mark the current node as visited.
        visited[v] = True

        # Recur for all the vertices adjacent to this vertex
        for i in self.graph[v]:
            if visited[i] is False:
                self.topological_sort_util(i, visited, stack)

        # Push current vertex to stack which stores result
        stack.insert(0, v)

    # The function to do Topological Sort. It uses recursive topologicalSortUtil()
    def topological_sort(self):
        # Mark all the vertices as not visited
        visited = [False] * self.V
        stack = []

        # Call the recursive helper function to store Topological Sort starting from all vertices one by one
        for i in range(self.V):
            if visited[i] is False:
                self.topological_sort_util(i, visited, stack)

        # return contents of stack
        return stack

    def is_cyclic_util(self, v, visited, recStack):

        # Mark current node as visited and adds to recursion stack
        visited[v] = True
        recStack[v] = True

        # Recur for all neighbours; if any neighbour is visited and in recStack then graph is cyclic
        for neighbour in self.graph[v]:
            if visited[neighbour] is False:
                if self.is_cyclic_util(neighbour, visited, recStack) is True:
                    return True
            elif recStack[neighbour] is True:
                return True

        # The node needs to be poped from recursion stack before function ends
        recStack[v] = False
        return False

    def is_cyclic(self):
        visited = [False] * self.V
        recStack = [False] * self.V
        for node in range(self.V):
            if visited[node] is False:
                if self.is_cyclic_util(node, visited, recStack) is True:
                    return True
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
    for elem in events:
        print(elem)
    g = Graph(len(events))
    for elem in events:
        if elem['AFTER-EVENT']:
            i = events.index(elem)
            j = 0
            temp = elem['AFTER-EVENT']
            for t in temp:
                for element in events:
                    if element['EVENT'] == t:
                        j = events.index(element)
                g.add_edge(j, i)
        if elem['BEFORE-EVENT']:
            i = events.index(elem)
            j = 0
            temp = elem['BEFORE-EVENT']
            for t in temp:
                for element in events:
                    if element['EVENT'] == t:
                        j = events.index(element)
                g.add_edge(i, j)
    if g.is_cyclic():
        print("there is a cycle")
    else:
        print("there is no cycle")
    sequence = g.topological_sort()
    print(sequence)
    for index in range(len(sequence)):
        for elem in range(len(event)):
            if sequence[index] == elem:
                print(events[elem])


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
