'''
Created on 11.11.2017

@author: user
'''
from coords import Transformation
import jpsElements
from main import Input
from constants import osm
from config import Config
from shapely.geometry import Polygon, LineString
from shapely.geometry.base import CAP_STYLE, JOIN_STYLE
from consistencyCheck import checkConsistency

class ElementHandler(object):
    '''
    classdocs
    '''
    def __init__(self):
        self.transform = Transformation(Input.tree.find(osm.Bounds))

    def handle(self, elem):
        print '---'
        print elem.attrib[osm.Id]
        wayRefs = []
        
        if elem.tag == osm.Way:
            #Way
            wayRefs.append(elem.attrib[osm.Id])
        elif elem.tag == osm.Relation:
            #Relation
            print 'Element:', elem.attrib[osm.Id], '--> Relation'
            for member in elem.iter(tag=osm.Member):
                if member.attrib[osm.Type] == osm.Way:
                    if member.attrib.get(osm.Role) == osm.Outer:
                        #outer member
                        print 'Outer Member -> Way'
                        wayRefs.append(member.attrib.get(osm.Ref))
                    elif member.attrib[osm.Role] == osm.Inner:
                        #inner member
                        print member.attrib[osm.Ref], 'is an inner Member -> Not handled yet!'
                    else:
                        #no outer/inner
                        print member.attrib[osm.Ref], 'is tagged: ', member.attrib[osm.Role], '--> no procedure implemented yet.'
        if wayRefs:
            for way in Input.tree.iter(tag=osm.Way):
                if way.attrib.get(osm.Id) in wayRefs:
                    self.way2polygon(way)
        else:
            print 'Element:', elem.attrib[osm.Id], 'is a:', elem.tag, '. How to handle this?' 
                
                
    def nodeRefs2XY(self, nodeRefs):
        XYList = []
        for nodeRef in nodeRefs:
            try:
                node = Input.nodes[nodeRef]
                lat = (node.attrib[osm.Lat])
                lon = (node.attrib[osm.Lon])
                x, y = self.transform.WGSToXY(lat, lon)
                XYList.append((x, y))
            except KeyError:
                print nodeRef, 'is not in the nodes list. ->OSM inconsistency?'
        return XYList
    
    def way2polygon(self, way):
        '''
        translate osm way to a shapely.geometry.polygon in order to to easily manipulate its shape.
        '''
        print  'wayent:', way.attrib[osm.Id], '--> Way'
        #area?
        area = False
        nodeRefs = []
        for child in way:
            if child.tag == osm.Tag: 
                try:
                    if child.attrib[osm.Value] in Config.areaTags[child.attrib[osm.Key]]:
                        area = True
                except KeyError:
                    pass
            if child.tag == osm.NodeRef:
                nodeRefs.append(child.attrib[osm.Ref])  
        XYList = self.nodeRefs2XY(nodeRefs)
        print 'NodeRefs:', nodeRefs
        print 'Coordinates:', XYList
        if area:
            #check if first and last nodes are the same
            if len(nodeRefs) > 2 and nodeRefs[0] == nodeRefs [-1]:
                #polygon
                poly = Polygon(XYList)
            else:
                #area == yes, but no polygon structure
                print  way.attrib[osm.Id], 'has wrong tags. Area=yes but first and last node references are not the same or less than 3 nodes'
                #continue as linestring?
        else:
            #LineString
            print way.attrib[osm.Id], 'is a LineString and needs to be buffered to create a Polygon.'
            ls = LineString(XYList)
            #polygon from linestring
            poly = ls.buffer(Config.stanardWidth/2, cap_style=CAP_STYLE.square, join_style=JOIN_STYLE.mitre, mitre_limit=Config.stanardWidth)
        
        poly = checkConsistency(poly, way)
        self.polygon2jps(poly, way)
        
    
    def polygon2jps(self, poly, elem):
        '''
        translate polygon to jps Elements with required attributes of the osm element
        '''
        print poly
        jpsRoom = jpsElements.Room(elem.attrib.get(osm.Id), elem.attrib.get(osm.Level))
        jpsSubroom = jpsElements.Subroom()
        jpsPoly = jpsElements.Polygon()
        for coord in poly.exterior._get_coords():
            jpsVertex = jpsElements.Vertex(str(coord[0]), str(coord[1]))
            jpsPoly.addVertex(jpsVertex)
        jpsSubroom.addPolygon(jpsPoly)
        jpsRoom.addSubroom(jpsSubroom)
        jpsElements.Geometry().addRoom(jpsRoom)
        
            
                