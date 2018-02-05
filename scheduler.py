import argparse
import logging
import ntpath
import os
from collections import defaultdict
from lxml import etree
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


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


def create_list(input_path, output_path, logger):
    current_path = os.path.realpath(__file__)
    head, tail = ntpath.split(current_path)
    xsd_path = head + '/AUTOSAR_4-2-2_STRICT.xsd'
    path = xsd_path.replace("\\", "/")
    events_rte = []
    events_aswc = []
    swc_allocation = []
    events = []
    for directory, directories, files in os.walk(input_path):
        for file in files:
            if file.endswith('.arxml'):
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
                ascre_event = root.findall(".//{http://autosar.org/schema/r4.0}ASYNCHRONOUS-SERVER-CALL-RETURNS-EVENT")
                for elem in ascre_event:
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
                    events_aswc.append(obj_event)
                be_event = root.findall(".//{http://autosar.org/schema/r4.0}BACKGROUND-EVENT")
                for elem in be_event:
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
                    events_aswc.append(obj_event)
                dree_event = root.findall(".//{http://autosar.org/schema/r4.0}DATA-RECEIVE-ERROR-EVENT")
                for elem in dree_event:
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
                    events_aswc.append(obj_event)
                dre_event = root.findall(".//{http://autosar.org/schema/r4.0}DATA-RECEIVED-EVENT")
                for elem in dre_event:
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
                    events_aswc.append(obj_event)
                dsce_event = root.findall(".//{http://autosar.org/schema/r4.0}DATA-SEND-COMPLETED-EVENT")
                for elem in dsce_event:
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
                    events_aswc.append(obj_event)
                dwce_event = root.findall(".//{http://autosar.org/schema/r4.0}DATA-WRITE-COMPLETED-EVENT")
                for elem in dwce_event:
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
                    events_aswc.append(obj_event)
                etoe_event = root.findall(".//{http://autosar.org/schema/r4.0}EXTERNAL-TRIGGER-OCCURRED-EVENT")
                for elem in etoe_event:
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
                    events_aswc.append(obj_event)
                ie_event = root.findall(".//{http://autosar.org/schema/r4.0}INIT-EVENT")
                for elem in ie_event:
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
                    events_aswc.append(obj_event)
                itoe_event = root.findall(".//{http://autosar.org/schema/r4.0}INTERNAL-TRIGGER-OCCURRED-EVENT")
                for elem in itoe_event:
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
                    events_aswc.append(obj_event)
                msae_event = root.findall(".//{http://autosar.org/schema/r4.0}MODE-SWITCHED-ACK-EVENT")
                for elem in msae_event:
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
                    events_aswc.append(obj_event)
                oie_event = root.findall(".//{http://autosar.org/schema/r4.0}OPERATION-INVOKED-EVENT")
                for elem in oie_event:
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
                    events_aswc.append(obj_event)
                smmee_event = root.findall(".//{http://autosar.org/schema/r4.0}SWC-MODE-MANAGER-ERROR-EVENT")
                for elem in smmee_event:
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
                    events_aswc.append(obj_event)
                smse_event = root.findall(".//{http://autosar.org/schema/r4.0}INTERNAL-TRIGGER-OCCURRED-EVENT")
                for elem in smse_event:
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
                    events_aswc.append(obj_event)
                te_event = root.findall(".//{http://autosar.org/schema/r4.0}TIMING-EVENT")
                for elem in te_event:
                    obj_event = {}
                    obj_event['NAME'] = elem.find('{http://autosar.org/schema/r4.0}SHORT-NAME').text
                    obj_event['TYPE'] = "PER"
                    obj_event['DURATION'] = "1µs"
                    obj_event['BEFORE-EVENT'] = ""
                    obj_event['AFTER-EVENT'] = ""
                    obj_event['CORE'] = ""
                    obj_event['ASIL'] = ""
                    if elem.find('{http://autosar.org/schema/r4.0}PERIOD') is not None:
                        obj_event['PERIOD'] = elem.find('{http://autosar.org/schema/r4.0}PERIOD').text
                    obj_event['ASWC'] = elem.getparent().getparent().getparent().getparent().getchildren()[0].text
                    events_aswc.append(obj_event)
                thee_event = root.findall(".//{http://autosar.org/schema/r4.0}TRANSFORMER-HARD-ERROR-EVENT")
                for elem in thee_event:
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
                    events_aswc.append(obj_event)
            if file.endswith('.xml'):
                fullname = os.path.join(directory, file)
                try:
                    check_if_xml_is_wellformed(fullname)
                    logger.info('The file: ' + fullname + ' is well-formed')
                except Exception as e:
                    logger.error('The file: ' + fullname + ' is not well-formed: ' + str(e))
                    return
                tree = etree.parse(fullname)
                root = tree.getroot()
                event = root.findall(".//EVENT")
                swc = root.findall(".//SWC-ALLOCATION")
                for element in event:
                    obj_event = {}
                    after_list = []
                    before_list = []
                    duration = None
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
                    events_rte.append(obj_event)
                for element in swc:
                    obj_event = {}
                    obj_event['SWC'] = element.find('SWC-REF').text
                    obj_event['CORE'] = element.find('CORE').text
                    obj_event['ASIL'] = element.find('ASIL').text
                    swc_allocation.append(obj_event)
    for elem_rte in events_rte:
        for elem_aswc in events_aswc:
            if elem_rte['EVENT'] == elem_aswc['NAME']:
                elem_aswc['BEFORE-EVENT'] = elem_rte['BEFORE-EVENT']
                elem_aswc['AFTER-EVENT'] = elem_rte['AFTER-EVENT']
                if elem_rte['DURATION'] is not None:
                    elem_aswc['DURATION'] = elem_rte['DURATION']
    for elem_swc in swc_allocation:
        for elem_aswc in events_aswc:
            if elem_swc['SWC'] == elem_aswc['ASWC']:
                elem_aswc['CORE'] = elem_swc['CORE']
                elem_aswc['ASIL'] = elem_swc['ASIL']
    #for elem in events_aswc:
    #    print(elem)
    g = Graph(len(events_aswc))
    for elem in events_aswc:
        if elem['AFTER-EVENT']:
            i = events_aswc.index(elem)
            j = 0
            temp = elem['AFTER-EVENT']
            for t in temp:
                for element in events_aswc:
                    if element['NAME'] == t:
                        j = events_aswc.index(element)
                g.add_edge(j, i)
        if elem['BEFORE-EVENT']:
            i = events_aswc.index(elem)
            j = 0
            temp = elem['BEFORE-EVENT']
            for t in temp:
                for element in events_aswc:
                    if element['NAME'] == t:
                        j = events_aswc.index(element)
                g.add_edge(i, j)
    if g.is_cyclic():
        logger.error('There is a cycle in task sequencing')
        return
    sequence = g.topological_sort()
    # setting the EventToTaskMapping parameter
    for index in range(len(sequence)):
        for elem in range(len(events_aswc)):
            if sequence[index] == elem:
                obj_event = {}
                obj_event['EVENT'] = events_aswc[elem]['NAME']
                obj_event['ACTIVATION-OFFSET'] = None
                obj_event['POSITION-IN-TASK'] = None
                try:
                    if events_aswc[elem]['CORE'] == '':
                        logger.error('CORE not set for SWC-REF:' + events_aswc[elem]['ASWC'])
                        return
                    elif events_aswc[elem]['ASIL'] == '':
                        logger.error('ASIL not set for SWC-REF:' + events_aswc[elem]['ASWC'])
                        return
                    else:
                        obj_event['MAPPED-TO-TASK'] = 'Task_'+events_aswc[elem]['CORE']+'_'+events_aswc[elem]['ASIL']+'_'+events_aswc[elem]['TYPE']
                except Exception:
                    logger.error('CORE or ASIL not set for SWC-REF:' + events_aswc[elem]['ASWC'])
                    return
                events.append(obj_event)
    # setting the PositionInTask parameter
    tasks = []
    for elem in events:
        if elem['MAPPED-TO-TASK'] not in tasks:
            tasks.append(elem['MAPPED-TO-TASK'])
    for task in tasks:
        count = 1
        for elem in events:
            if elem['MAPPED-TO-TASK'] == task:
                elem['POSITION-IN-TASK'] = count
                count = count + 1
    for elem in events:
        print(elem)
    # for elem in tasks:
    #     print(elem)


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
