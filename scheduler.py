import argparse
import logging
import ntpath
import os
import xml.etree.ElementTree as ET
from collections import defaultdict
from decimal import Decimal
from lxml import etree
from xml.dom import minidom
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


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
    input_path = input_path.split(';')
    output_path = output_directory.replace("\\", "/")
    # logger creation and setting
    logger = logging.getLogger('result')
    hdlr = logging.FileHandler(output_path + '/result.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.INFO)
    open(output_path + '/result.log', 'w').close()
    events = []
    create_list(input_path, events, logger)
    create_script(events, output_path, logger)


def arg_parse(parser):
    # adding command line options
    parser.add_argument("-in", action="store_const", const='-in')
    parser.add_argument("input_directory", help="location(s) of input files")
    parser.add_argument("-out", action="store_const", const='-out')
    parser.add_argument("output_path", help="folder which will contain the produced files")


def create_list(input_path, events, logger):
    current_path = os.path.realpath(__file__)
    head, tail = ntpath.split(current_path)
    xsd_path = head + '/AUTOSAR_4-2-2_STRICT.xsd'
    path = xsd_path.replace("\\", "/")
    events_rte = []
    events_aswc = []
    swc_allocation = []
    xdm_events = []
    for each_path in input_path:
        for directory, directories, files in os.walk(each_path):
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
                        obj_event['DURATION'] = "0.01"
                        obj_event['BEFORE-EVENT'] = []
                        obj_event['AFTER-EVENT'] = []
                        obj_event['CORE'] = ""
                        obj_event['ASIL'] = ""
                        if elem.find('{http://autosar.org/schema/r4.0}PERIOD') is not None:
                            obj_event['PERIOD'] = elem.find('{http://autosar.org/schema/r4.0}PERIOD').text
                        else:
                            obj_event['PERIOD'] = None
                        obj_event['ASWC'] = elem.getparent().getparent().getparent().getparent().getchildren()[0].text
                        events_aswc.append(obj_event)
                    be_event = root.findall(".//{http://autosar.org/schema/r4.0}BACKGROUND-EVENT")
                    for elem in be_event:
                        obj_event = {}
                        obj_event['NAME'] = elem.find('{http://autosar.org/schema/r4.0}SHORT-NAME').text
                        obj_event['TYPE'] = "EVT"
                        obj_event['DURATION'] = "0.01"
                        obj_event['BEFORE-EVENT'] = []
                        obj_event['AFTER-EVENT'] = []
                        obj_event['CORE'] = ""
                        obj_event['ASIL'] = ""
                        if elem.find('{http://autosar.org/schema/r4.0}PERIOD') is not None:
                            obj_event['PERIOD'] = elem.find('{http://autosar.org/schema/r4.0}PERIOD').text
                        else:
                            obj_event['PERIOD'] = None
                        obj_event['ASWC'] = elem.getparent().getparent().getparent().getparent().getchildren()[0].text
                        events_aswc.append(obj_event)
                    dree_event = root.findall(".//{http://autosar.org/schema/r4.0}DATA-RECEIVE-ERROR-EVENT")
                    for elem in dree_event:
                        obj_event = {}
                        obj_event['NAME'] = elem.find('{http://autosar.org/schema/r4.0}SHORT-NAME').text
                        obj_event['TYPE'] = "EVT"
                        obj_event['DURATION'] = "0.01"
                        obj_event['BEFORE-EVENT'] = []
                        obj_event['AFTER-EVENT'] = []
                        obj_event['CORE'] = ""
                        obj_event['ASIL'] = ""
                        if elem.find('{http://autosar.org/schema/r4.0}PERIOD') is not None:
                            obj_event['PERIOD'] = elem.find('{http://autosar.org/schema/r4.0}PERIOD').text
                        else:
                            obj_event['PERIOD'] = None
                        obj_event['ASWC'] = elem.getparent().getparent().getparent().getparent().getchildren()[0].text
                        events_aswc.append(obj_event)
                    dre_event = root.findall(".//{http://autosar.org/schema/r4.0}DATA-RECEIVED-EVENT")
                    for elem in dre_event:
                        obj_event = {}
                        obj_event['NAME'] = elem.find('{http://autosar.org/schema/r4.0}SHORT-NAME').text
                        obj_event['TYPE'] = "EVT"
                        obj_event['DURATION'] = "0.01"
                        obj_event['BEFORE-EVENT'] = []
                        obj_event['AFTER-EVENT'] = []
                        obj_event['CORE'] = ""
                        obj_event['ASIL'] = ""
                        if elem.find('{http://autosar.org/schema/r4.0}PERIOD') is not None:
                            obj_event['PERIOD'] = elem.find('{http://autosar.org/schema/r4.0}PERIOD').text
                        else:
                            obj_event['PERIOD'] = None
                        obj_event['ASWC'] = elem.getparent().getparent().getparent().getparent().getchildren()[0].text
                        events_aswc.append(obj_event)
                    dsce_event = root.findall(".//{http://autosar.org/schema/r4.0}DATA-SEND-COMPLETED-EVENT")
                    for elem in dsce_event:
                        obj_event = {}
                        obj_event['NAME'] = elem.find('{http://autosar.org/schema/r4.0}SHORT-NAME').text
                        obj_event['TYPE'] = "EVT"
                        obj_event['DURATION'] = "0.01"
                        obj_event['BEFORE-EVENT'] = []
                        obj_event['AFTER-EVENT'] = []
                        obj_event['CORE'] = ""
                        obj_event['ASIL'] = ""
                        if elem.find('{http://autosar.org/schema/r4.0}PERIOD') is not None:
                            obj_event['PERIOD'] = elem.find('{http://autosar.org/schema/r4.0}PERIOD').text
                        else:
                            obj_event['PERIOD'] = None
                        obj_event['ASWC'] = elem.getparent().getparent().getparent().getparent().getchildren()[0].text
                        events_aswc.append(obj_event)
                    dwce_event = root.findall(".//{http://autosar.org/schema/r4.0}DATA-WRITE-COMPLETED-EVENT")
                    for elem in dwce_event:
                        obj_event = {}
                        obj_event['NAME'] = elem.find('{http://autosar.org/schema/r4.0}SHORT-NAME').text
                        obj_event['TYPE'] = "EVT"
                        obj_event['DURATION'] = "0.01"
                        obj_event['BEFORE-EVENT'] = []
                        obj_event['AFTER-EVENT'] = []
                        obj_event['CORE'] = ""
                        obj_event['ASIL'] = ""
                        if elem.find('{http://autosar.org/schema/r4.0}PERIOD') is not None:
                            obj_event['PERIOD'] = elem.find('{http://autosar.org/schema/r4.0}PERIOD').text
                        else:
                            obj_event['PERIOD'] = None
                        obj_event['ASWC'] = elem.getparent().getparent().getparent().getparent().getchildren()[0].text
                        events_aswc.append(obj_event)
                    etoe_event = root.findall(".//{http://autosar.org/schema/r4.0}EXTERNAL-TRIGGER-OCCURRED-EVENT")
                    for elem in etoe_event:
                        obj_event = {}
                        obj_event['NAME'] = elem.find('{http://autosar.org/schema/r4.0}SHORT-NAME').text
                        obj_event['TYPE'] = "EVT"
                        obj_event['DURATION'] = "0.01"
                        obj_event['BEFORE-EVENT'] = []
                        obj_event['AFTER-EVENT'] = []
                        obj_event['CORE'] = ""
                        obj_event['ASIL'] = ""
                        if elem.find('{http://autosar.org/schema/r4.0}PERIOD') is not None:
                            obj_event['PERIOD'] = elem.find('{http://autosar.org/schema/r4.0}PERIOD').text
                        else:
                            obj_event['PERIOD'] = None
                        obj_event['ASWC'] = elem.getparent().getparent().getparent().getparent().getchildren()[0].text
                        events_aswc.append(obj_event)
                    ie_event = root.findall(".//{http://autosar.org/schema/r4.0}INIT-EVENT")
                    for elem in ie_event:
                        obj_event = {}
                        obj_event['NAME'] = elem.find('{http://autosar.org/schema/r4.0}SHORT-NAME').text
                        obj_event['TYPE'] = "EVT"
                        obj_event['DURATION'] = "0.01"
                        obj_event['BEFORE-EVENT'] = []
                        obj_event['AFTER-EVENT'] = []
                        obj_event['CORE'] = ""
                        obj_event['ASIL'] = ""
                        if elem.find('{http://autosar.org/schema/r4.0}PERIOD') is not None:
                            obj_event['PERIOD'] = elem.find('{http://autosar.org/schema/r4.0}PERIOD').text
                        else:
                            obj_event['PERIOD'] = None
                        obj_event['ASWC'] = elem.getparent().getparent().getparent().getparent().getchildren()[0].text
                        events_aswc.append(obj_event)
                    itoe_event = root.findall(".//{http://autosar.org/schema/r4.0}INTERNAL-TRIGGER-OCCURRED-EVENT")
                    for elem in itoe_event:
                        obj_event = {}
                        obj_event['NAME'] = elem.find('{http://autosar.org/schema/r4.0}SHORT-NAME').text
                        obj_event['TYPE'] = "EVT"
                        obj_event['DURATION'] = "0.01"
                        obj_event['BEFORE-EVENT'] = []
                        obj_event['AFTER-EVENT'] = []
                        obj_event['CORE'] = ""
                        obj_event['ASIL'] = ""
                        if elem.find('{http://autosar.org/schema/r4.0}PERIOD') is not None:
                            obj_event['PERIOD'] = elem.find('{http://autosar.org/schema/r4.0}PERIOD').text
                        else:
                            obj_event['PERIOD'] = None
                        obj_event['ASWC'] = elem.getparent().getparent().getparent().getparent().getchildren()[0].text
                        events_aswc.append(obj_event)
                    msae_event = root.findall(".//{http://autosar.org/schema/r4.0}MODE-SWITCHED-ACK-EVENT")
                    for elem in msae_event:
                        obj_event = {}
                        obj_event['NAME'] = elem.find('{http://autosar.org/schema/r4.0}SHORT-NAME').text
                        obj_event['TYPE'] = "EVT"
                        obj_event['DURATION'] = "0.01"
                        obj_event['BEFORE-EVENT'] = []
                        obj_event['AFTER-EVENT'] = []
                        obj_event['CORE'] = ""
                        obj_event['ASIL'] = ""
                        if elem.find('{http://autosar.org/schema/r4.0}PERIOD') is not None:
                            obj_event['PERIOD'] = elem.find('{http://autosar.org/schema/r4.0}PERIOD').text
                        else:
                            obj_event['PERIOD'] = None
                        obj_event['ASWC'] = elem.getparent().getparent().getparent().getparent().getchildren()[0].text
                        events_aswc.append(obj_event)
                    oie_event = root.findall(".//{http://autosar.org/schema/r4.0}OPERATION-INVOKED-EVENT")
                    for elem in oie_event:
                        obj_event = {}
                        obj_event['NAME'] = elem.find('{http://autosar.org/schema/r4.0}SHORT-NAME').text
                        obj_event['TYPE'] = "EVT"
                        obj_event['DURATION'] = "0.01"
                        obj_event['BEFORE-EVENT'] = []
                        obj_event['AFTER-EVENT'] = []
                        obj_event['CORE'] = ""
                        obj_event['ASIL'] = ""
                        if elem.find('{http://autosar.org/schema/r4.0}PERIOD') is not None:
                            obj_event['PERIOD'] = elem.find('{http://autosar.org/schema/r4.0}PERIOD').text
                        else:
                            obj_event['PERIOD'] = None
                        obj_event['ASWC'] = elem.getparent().getparent().getparent().getparent().getchildren()[0].text
                        events_aswc.append(obj_event)
                    smmee_event = root.findall(".//{http://autosar.org/schema/r4.0}SWC-MODE-MANAGER-ERROR-EVENT")
                    for elem in smmee_event:
                        obj_event = {}
                        obj_event['NAME'] = elem.find('{http://autosar.org/schema/r4.0}SHORT-NAME').text
                        obj_event['TYPE'] = "EVT"
                        obj_event['DURATION'] = "0.01"
                        obj_event['BEFORE-EVENT'] = []
                        obj_event['AFTER-EVENT'] = []
                        obj_event['CORE'] = ""
                        obj_event['ASIL'] = ""
                        if elem.find('{http://autosar.org/schema/r4.0}PERIOD') is not None:
                            obj_event['PERIOD'] = elem.find('{http://autosar.org/schema/r4.0}PERIOD').text
                        else:
                            obj_event['PERIOD'] = None
                        obj_event['ASWC'] = elem.getparent().getparent().getparent().getparent().getchildren()[0].text
                        events_aswc.append(obj_event)
                    smse_event = root.findall(".//{http://autosar.org/schema/r4.0}INTERNAL-TRIGGER-OCCURRED-EVENT")
                    for elem in smse_event:
                        obj_event = {}
                        obj_event['NAME'] = elem.find('{http://autosar.org/schema/r4.0}SHORT-NAME').text
                        obj_event['TYPE'] = "EVT"
                        obj_event['DURATION'] = "0.01"
                        obj_event['BEFORE-EVENT'] = []
                        obj_event['AFTER-EVENT'] = []
                        obj_event['CORE'] = ""
                        obj_event['ASIL'] = ""
                        if elem.find('{http://autosar.org/schema/r4.0}PERIOD') is not None:
                            obj_event['PERIOD'] = elem.find('{http://autosar.org/schema/r4.0}PERIOD').text
                        else:
                            obj_event['PERIOD'] = None
                        obj_event['ASWC'] = elem.getparent().getparent().getparent().getparent().getchildren()[0].text
                        events_aswc.append(obj_event)
                    te_event = root.findall(".//{http://autosar.org/schema/r4.0}TIMING-EVENT")
                    for elem in te_event:
                        obj_event = {}
                        obj_event['NAME'] = elem.find('{http://autosar.org/schema/r4.0}SHORT-NAME').text
                        obj_event['TYPE'] = "PER"
                        obj_event['DURATION'] = "0.01"
                        obj_event['BEFORE-EVENT'] = []
                        obj_event['AFTER-EVENT'] = []
                        obj_event['CORE'] = ""
                        obj_event['ASIL'] = ""
                        if elem.find('{http://autosar.org/schema/r4.0}PERIOD') is not None:
                            obj_event['PERIOD'] = elem.find('{http://autosar.org/schema/r4.0}PERIOD').text
                        else:
                            obj_event['PERIOD'] = None
                        obj_event['ASWC'] = elem.getparent().getparent().getparent().getparent().getchildren()[0].text
                        events_aswc.append(obj_event)
                    thee_event = root.findall(".//{http://autosar.org/schema/r4.0}TRANSFORMER-HARD-ERROR-EVENT")
                    for elem in thee_event:
                        obj_event = {}
                        obj_event['NAME'] = elem.find('{http://autosar.org/schema/r4.0}SHORT-NAME').text
                        obj_event['TYPE'] = "EVT"
                        obj_event['DURATION'] = "0.01"
                        obj_event['BEFORE-EVENT'] = []
                        obj_event['AFTER-EVENT'] = []
                        obj_event['CORE'] = ""
                        obj_event['ASIL'] = ""
                        if elem.find('{http://autosar.org/schema/r4.0}PERIOD') is not None:
                            obj_event['PERIOD'] = elem.find('{http://autosar.org/schema/r4.0}PERIOD').text
                        else:
                            obj_event['PERIOD'] = None
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
                if file.endswith('.xdm'):
                    fullname = os.path.join(directory, file)
                    try:
                        check_if_xml_is_wellformed(fullname)
                        logger.info('The file: ' + fullname + ' is well-formed')
                    except Exception as e:
                        logger.error('The file: ' + fullname + ' is not well-formed: ' + str(e))
                        return
                    tree = etree.parse(fullname)
                    root = tree.getroot()
                    nsmap = {}
                    for ns in tree.xpath('//namespace::*'):
                        if ns[0]:  # Removes the None namespace, neither needed nor supported.
                            nsmap[ns[0]] = ns[1]
                    xdm_event = root.findall('.//{http://www.tresos.de/_projects/DataModel2/06/data.xsd}ctr')
                    for elem in xdm_event[:]:
                        try:
                            if elem.getparent().getparent().getparent().attrib['name'] != "RteSwComponentInstance":
                                xdm_event.remove(elem)
                        except Exception:
                            xdm_event.remove(elem)
                    for elem in xdm_event:
                        obj_event = {}
                        obj_event['NAME'] = elem.attrib['name']
                        if elem.find('.//{http://www.tresos.de/_projects/DataModel2/06/data.xsd}var[@name = "RteActivationOffset"]') is not None:
                            obj_event['ACTIVATION-OFFSET'] = elem.find('.//{http://www.tresos.de/_projects/DataModel2/06/data.xsd}var[@name = "RteActivationOffset"]').attrib['value']
                        else:
                            obj_event['ACTIVATION-OFFSET'] = "NotSet"
                        if elem.find('.//{http://www.tresos.de/_projects/DataModel2/06/data.xsd}var[@name = "RtePositionInTask"]') is not None:
                            obj_event['POSITION-IN-TASK'] = elem.find('.//{http://www.tresos.de/_projects/DataModel2/06/data.xsd}var[@name = "RtePositionInTask"]').attrib['value']
                        else:
                            obj_event['POSITION-IN-TASK'] = "NotSet"
                        if elem.find('.//{http://www.tresos.de/_projects/DataModel2/06/data.xsd}var[@name = "RteMappedToTaskRef"]') is not None:
                            obj_event['MAPPED-TO-TASK'] = elem.find('.//{http://www.tresos.de/_projects/DataModel2/06/data.xsd}var[@name = "RteMappedToTaskRef"]').attrib['value']
                        else:
                            obj_event['MAPPED-TO-TASK'] = "NotSet"
                        xdm_events.append(obj_event)

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
                except Exception as e:
                    logger.error('CORE or ASIL not set for SWC-REF:' + events_aswc[elem]['ASWC'] + " -> " + str(e))
                    return
                # obj_event['MAPPED-TO-TASK'] = 'Task_'+events_aswc[elem]['CORE']+'_'+events_aswc[elem]['ASIL']+'_'+events_aswc[elem]['TYPE']
                obj_event['PERIOD'] = events_aswc[elem]['PERIOD']
                obj_event['DURATION'] = events_aswc[elem]['DURATION']
                obj_event['AFTER-EVENT'] = events_aswc[elem]['AFTER-EVENT']
                obj_event['BEFORE-EVENT'] = events_aswc[elem]['BEFORE-EVENT']
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
    # setting the RteActivationOffset parameter
    offset = 0
    for elem in events:
        elem['ACTIVATION-OFFSET'] = offset
        offset = offset + float(Decimal(elem['DURATION']))

    # check not to overwrite existing data from base xmd
    for elem_task in events:
        for elem_xdm in xdm_events:
            if elem_task['EVENT'] == elem_xdm['NAME']:
                if elem_xdm['ACTIVATION-OFFSET'] != "NotSet":
                    elem_task['ACTIVATION-OFFSET'] = elem_xdm['ACTIVATION-OFFSET']
                if elem_xdm['POSITION-IN-TASK'] != "NotSet":
                    elem_task['POSITION-IN-TASK'] = elem_xdm['POSITION-IN-TASK']
                if elem_xdm['MAPPED-TO-TASK'] != "NotSet":
                    elem_task['MAPPED-TO-TASK'] = elem_xdm['MAPPED-TO-TASK']
    # for elem in events:
    #     print(elem)


def create_script(events, output_path, logger):
    root_script = ET.Element('Script')
    root_script.set('xsi:noNamespaceSchemaLocation', "Scriptor.xsd")
    root_script.set('xmlns:xsi', "http://www.w3.org/2001/XMLSchema-instance")
    name = ET.SubElement(root_script, 'Name').text = "RTE_Config"
    decription = ET.SubElement(root_script, 'Decription').text = "Set the RTE parameters"
    expression = ET.SubElement(root_script, 'Expression').text = "as:modconf('Rte')[1]"
    operations_global = ET.SubElement(root_script, 'Operations')
    for event in events:
        operation = ET.SubElement(operations_global, 'Operation')
        operation.set('Type', "ForEach")
        expression_global = ET.SubElement(operation, 'Expression')
        expression_global.text = './/d:lst[name="RteSwComponentInstance"]/d:ctr/d:lst/d:ctr[name="'+event['EVENT']+'"]'
        operations = ET.SubElement(operation, 'Operations')
        operation_offset = ET.SubElement(operations, 'Operation')
        operation_offset.set('Type', "Add")
        expression_offset = ET.SubElement(operation_offset, 'Expression')
        expression_offset.text = './/d:lst[name="RteSwComponentInstance"]/d:ctr/d:lst/d:ctr[name="'+event['EVENT']+'"]/d:var[name="RteActivationOffset"]'
        operations_activation = ET.SubElement(operation_offset, "Operations")
        operation_element = ET.SubElement(operations_activation, "Operation")
        operation_element.set('Type', "SetValue")
        expression_element = ET.SubElement(operation_element, "Expression").text = '"' + str(event['ACTIVATION-OFFSET']) + '"'
        operation_position = ET.SubElement(operations, 'Operation')
        operation_position.set('Type', "Add")
        expression_position = ET.SubElement(operation_position, 'Expression')
        expression_position.text = './/d:lst[name="RteSwComponentInstance"]/d:ctr/d:lst/d:ctr[name="'+event['EVENT']+'"]/d:var[name="RtePositionInTask"]'
        operations_activation = ET.SubElement(operation_position, "Operations")
        operation_element = ET.SubElement(operations_activation, "Operation")
        operation_element.set('Type', "SetValue")
        expression_element = ET.SubElement(operation_element, "Expression").text = '"' + str(event['POSITION-IN-TASK']) + '"'
        operation_task = ET.SubElement(operations, 'Operation')
        operation_task.set('Type', "Add")
        expression_task = ET.SubElement(operation_task, 'Expression')
        expression_task.text = './/d:lst[name="RteSwComponentInstance"]/d:ctr/d:lst/d:ctr[name="'+event['EVENT']+'"]/d:var[name="RteMappedToTaskRef"]'
        operations_activation = ET.SubElement(operation_task, "Operations")
        operation_element = ET.SubElement(operations_activation, "Operation")
        operation_element.set('Type', "SetValue")
        expression_element = ET.SubElement(operation_element, "Expression").text = '"ASPath:/Os/Os/' + str(event['MAPPED-TO-TASK'] + '"')

    pretty_xml = prettify_xml(root_script)
    tree = ET.ElementTree(ET.fromstring(pretty_xml))
    tree.write(output_path + "/RTE_script.xml", encoding="UTF-8", xml_declaration=True, method="xml")


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


def prettify_xml(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="    ")


def check_if_xml_is_wellformed(file):
    parser = make_parser()
    parser.setContentHandler(ContentHandler())
    parser.parse(file)


if __name__ == "__main__":
        main()
