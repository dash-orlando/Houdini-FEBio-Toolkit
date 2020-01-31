import xml.dom.minidom as minidom
from decimal import Decimal


def parse_feb(file):
    return FebObject(file)


def write_feb(feb, file):
    string = str(feb)

    f = open(file, "w")
    f.write(string)
    f.close()

    return string


# A data type that contains the info stored in a FEB object
class FebObject:
    def __init__(self, file=None, name="geometry"):

        self.name = name
        self.file_path = file
        if file is not None:
            self.xml_document = minidom.parse(file)
        else:
            self.xml_document = None

        # Setting Values
        self.controls = {}
        self.time_stepper = {}
        self.analysis_type = "static"
        self.globals = {}

        # Geometry Data
        self.materials = []
        self.nodes = []
        self.tets = []
        self.groups = []
        self.parts = []

        # Simulation Data
        self.boundary_conditions = []
        self.load_curves = []
        self.loads = []

        # Output Data
        self.plot_data = []
        self.logged_node_data = []
        self.logged_tet_data = []

        if file is not None:
            self.build()

    def __str__(self):
        doc = minidom.Document()
        debug_depth = 10
        feb = self

        # febio_spec will span the whole document
        febio_spec = doc.createElement('febio_spec')
        febio_spec.setAttribute('version', '2.5')
        doc.appendChild(febio_spec)

        if debug_depth >= 0:
            # --- BEGIN MODULE --- #
            module = doc.createElement('Module')
            module.setAttribute("type", "solid")
            febio_spec.appendChild(module)
            # --- END MODULE --- #

        if debug_depth >= 1:
            # --- BEGIN CONTROL --- #
            control = doc.createElement('Control')
            febio_spec.appendChild(control)
            for node in feb.controls:
                elem = doc.createElement(str(node))
                elem.appendChild(doc.createTextNode(str(feb.controls[node])))
                control.appendChild(elem)
            time_stepper = doc.createElement('time_stepper')
            control.appendChild(time_stepper)
            for ts in feb.time_stepper:
                elem = doc.createElement(str(ts))
                elem.appendChild(doc.createTextNode(str(feb.time_stepper[ts])))
                time_stepper.appendChild(elem)
            analysis = doc.createElement('analysis')
            analysis.setAttribute('type', str(feb.analysis_type))
            control.appendChild(analysis)
            # --- END CONTROL --- #

        if debug_depth >= 2:
            # --- BEGIN GLOBALS --- #
            globals = doc.createElement('Globals')
            febio_spec.appendChild(globals)

            if debug_depth >= 2.1:
                # --- BEGIN CONSTANTS --- #
                constants = doc.createElement('Constants')

                t = doc.createElement('T')
                t.appendChild(doc.createTextNode('0'))
                r = doc.createElement('R')
                r.appendChild(doc.createTextNode('0'))
                fc = doc.createElement('Fc')
                fc.appendChild(doc.createTextNode('0'))

                constants.appendChild(t)
                constants.appendChild(r)
                constants.appendChild(fc)
                # --- END CONSTANTS --- #

                globals.appendChild(constants)
            # --- END GLOBALS --- #

        if debug_depth >= 3:
            # --- BEGIN MATERIALS --- #
            material = doc.createElement('Material')
            febio_spec.appendChild(material)

            for mat in feb.materials:
                nmat = doc.createElement('material')
                nmat.setAttribute('id', str(mat.id))
                nmat.setAttribute('name', str(mat.name))
                nmat.setAttribute('type', str(mat.type))

                density = doc.createElement('density')
                density.appendChild(doc.createTextNode(str(mat.dens)))
                nmat.appendChild(density)

                e = doc.createElement('E')
                e.appendChild(doc.createTextNode(str(mat.e)))
                nmat.appendChild(e)

                v = doc.createElement('v')
                v.appendChild(doc.createTextNode(str(mat.v)))
                nmat.appendChild(v)

                material.appendChild(nmat)
            # --- END MATERIALS --- #

        if debug_depth >= 4:
            # --- BEGIN GEOMETRY --- #
            geometry = doc.createElement('Geometry')
            febio_spec.appendChild(geometry)

            if debug_depth >= 4.1:
                # --- BEGIN NODES --- #
                nodes = doc.createElement('Nodes')
                nodes.setAttribute('name', str(feb.name))

                for node in feb.nodes:
                    nnode = doc.createElement('node')
                    nnode.setAttribute('id', str(node.idBio))
                    nnode.appendChild(doc.createTextNode(str(point_to_node(node))))
                    nodes.appendChild(nnode)

                geometry.appendChild(nodes)
                # --- END NODES --- #
            if debug_depth >= 4.2:
                # --- BEGIN ELEMENTS --- #
                for part in feb.parts:
                    element = doc.createElement('Elements')
                    element.setAttribute('type', 'tet4')
                    element.setAttribute('mat', str(part.material.id))
                    element.setAttribute('name', str(part.name))

                    for tet in part.tets:
                        elem = doc.createElement('elem')
                        elem.setAttribute('id', str(tet.idBio))
                        elem.appendChild(doc.createTextNode(tet_to_elem(tet)))
                        element.appendChild(elem)

                    geometry.appendChild(element)
                # --- END ELEMENTS --- #
            if debug_depth >= 4.3:
                # --- BEGIN NODESET --- #
                for group in feb.groups:
                    node_set = doc.createElement('NodeSet')
                    node_set.setAttribute('name', str(group.name))

                    for node in group.nodes:
                        nnode = doc.createElement('node')
                        nnode.setAttribute('id', str(node.idBio))
                        node_set.appendChild(nnode)

                    geometry.appendChild(node_set)
                # --- END NODESET --- #

            # --- END GEOMETRY --- #

        if debug_depth >= 5:
            # --- BEGIN BOUNDARY --- #
            boundary = doc.createElement('Boundary')
            for boundary_condition in feb.boundary_conditions:
                type = boundary_condition.type
                nbc = doc.createElement(str(type))
                nbc.setAttribute('bc', str(boundary_condition.bc))
                nbc.setAttribute('node_set', str(boundary_condition.node_set))
                if debug_depth >= 5.1:
                    if type == "prescribe":
                        for param in boundary_condition.params:
                            elem = doc.createElement(str(param))
                            elem.appendChild(doc.createTextNode(str(boundary_condition.params[param])))
                            if param == "scale":
                                elem.setAttribute('lc', str(boundary_condition.curve))

                            nbc.appendChild(elem)
                boundary.appendChild(nbc)

            febio_spec.appendChild(boundary)
            # --- END BOUNDARY --- #

        # --- BEGIN LOADS --- #
        if debug_depth > 6:
            loads = doc.createElement('Loads')

            if debug_depth > 6.1:
                if len(feb.loads) > 0:
                    for load in feb.loads:
                        nload = doc.createElement('body_load')
                        nload.setAttribute('type', str(load.type))
                        nload.setAttribute('elem_set', str(load.part.name))

                        x = doc.createElement('x')
                        x.setAttribute('lc', str(load.x_curve.id))
                        x.appendChild(doc.createTextNode(str(load.x)))
                        nload.appendChild(x)

                        y = doc.createElement('y')
                        y.setAttribute('lc', str(load.y_curve.id))
                        y.appendChild(doc.createTextNode(str(load.y)))
                        nload.appendChild(y)

                        z = doc.createElement('z')
                        z.setAttribute('lc', str(load.z_curve.id))
                        z.appendChild(doc.createTextNode(str(load.z)))
                        nload.appendChild(z)

                        loads.appendChild(nload)

            febio_spec.appendChild(loads)
        # --- END LOADS --- #


        if debug_depth >= 7:
            # --- BEGIN LOADDATA --- #
            load_data = doc.createElement('LoadData')

            if debug_depth >= 7.1:
                # --- BEGIN LOADCURVE --- #
                for lc in feb.load_curves:
                    curve = doc.createElement('loadcurve')
                    curve.setAttribute('id', str(lc.id))
                    curve.setAttribute('type', str(lc.type))
                    if debug_depth >= 6.11:
                        for pt in lc.points:
                            npt = doc.createElement('point')
                            npt.appendChild(doc.createTextNode(','.join(pt)))
                            curve.appendChild(npt)
                    load_data.appendChild(curve)
                # --- END LOADCURVE --- #

            febio_spec.appendChild(load_data)
            # --- END LOADDATA --- #

        if debug_depth >= 8:
            # --- BEGIN OUTPUT --- #
            output = doc.createElement('Output')
            febio_spec.appendChild(output)

            if debug_depth >= 8.1:
                # --- BEGIN PLOTFILE --- #
                plotfile = doc.createElement('plotfile')
                plotfile.setAttribute('type', "febio")

                disp = doc.createElement('var')
                disp.setAttribute('type', 'displacement')
                plotfile.appendChild(disp)

                stress = doc.createElement('var')
                stress.setAttribute('type', 'stress')
                plotfile.appendChild(stress)

                output.appendChild(plotfile)
                # --- END PLOTFILE --- #

            if debug_depth >= 8.2:
                # --- BEGIN LOGFILE --- #
                logfile = doc.createElement('logfile')

                if feb.logged_node_data != [] and feb.logged_node_data != [""]:
                    node_data = doc.createElement('node_data')
                    node_data.setAttribute('data', ";".join(feb.logged_node_data))
                    logfile.appendChild(node_data)

                if feb.logged_tet_data != [] and feb.logged_tet_data != [""]:
                    element_data = doc.createElement('element_data')
                    element_data.setAttribute('data', ";".join(feb.logged_tet_data))
                    logfile.appendChild(element_data)

                output.appendChild(logfile)
                # --- END LOGFILE --- #

            # --- END OUTPUT --- #

        # --- END --- #
        return doc.toprettyxml()

    def build(self):
        # Read in settings
        control_tag = self.xml_document.getElementsByTagName("Control")[0]
        for node in control_tag.childNodes:
            if node.nodeType == node.TEXT_NODE:
                continue

            if node.tagName == "time_stepper":
                for ts_node in node.childNodes:
                    if ts_node.nodeType == node.TEXT_NODE:
                        continue
                    self.time_stepper[str(ts_node.tagName)] = ts_node.firstChild.nodeValue
                continue
            elif node.tagName == "analysis":
                self.analysis_type = node.getAttribute("type")
            else:
                try:
                    self.controls[str(node.tagName)] = node.firstChild.nodeValue
                except:
                    print("Couldn't parse control {}".format(node))

        # Read in materials
        materials = self.xml_document.getElementsByTagName("Material")[0]
        for material in materials.childNodes:
            if material.nodeType == node.TEXT_NODE:
                continue

            id = material.getAttribute("id")
            name = material.getAttribute("name")
            type = material.getAttribute("type")

            dens = material.childNodes[1].firstChild.nodeValue
            e = material.childNodes[3].firstChild.nodeValue
            v = material.childNodes[5].firstChild.nodeValue

            self.materials.append(Material(id, name, dens, e, v, type=type))

        # Read Geometry values
        # Nodes
        nodes_xml = self.xml_document.getElementsByTagName("Nodes")[0]
        node_list_xml = nodes_xml.getElementsByTagName("node")
        for node in node_list_xml:
            x, y, z = node_to_point(node.firstChild.nodeValue)
            id = int(node.getAttribute("id"))
            self.nodes.append(Point(x, y, z, id))

        # Tetrahedrons
        parts_xml = self.xml_document.getElementsByTagName("Elements")
        for part in parts_xml:
            new_part = Part(part.getAttribute("name"))
            new_part.material = self.get_mat_by_id(int(part.getAttribute("mat")))
            tet_list_xml = part.getElementsByTagName("elem")
            for tet in tet_list_xml:
                p0, p1, p2, p3 = elem_to_tet(tet.firstChild.nodeValue)
                id = int(tet.getAttribute("id"))
                ntet = Tet(p0, p1, p2, p3, id)
                self.tets.append( ntet )
                new_part.tets.append( ntet )
            self.parts.append(new_part)

        # Groups
        groups_xml = self.xml_document.getElementsByTagName("NodeSet")
        for group in groups_xml:
            points = []
            node_list = group.getElementsByTagName("node")
            for node in node_list:
                points.append(self.get_node_by_id(int(node.getAttribute("id"))))

            self.groups.append(Group(group.getAttribute("name"), points))

        # Boundary Conditions
        boundary_xml = self.xml_document.getElementsByTagName("Boundary")[0]
        for boundary in boundary_xml.childNodes:
            if boundary.nodeType == boundary.TEXT_NODE:
                continue
            type = boundary.tagName
            bc = boundary.getAttribute("bc")
            group_name = boundary.getAttribute("node_set")
            group = self.get_grp_by_name(group_name)
            if group is None:
                group = group_name
                print "Group not found in internal node groups"
            nbc = Boundary(group, type, bc=bc)
            if type == "prescribe":
                scale = boundary.getElementsByTagName("scale")[0].firstChild.nodeValue
                rel = boundary.getElementsByTagName("relative")[0].firstChild.nodeValue
                nbc.params["scale"] = scale
                nbc.params["relative"] = rel
                nbc.curve = boundary.getElementsByTagName("scale")[0].getAttribute("lc")

            self.boundary_conditions.append(nbc)

        # LoadData
        loaddata_xml = self.xml_document.getElementsByTagName("LoadData")[0]
        for load_curve in loaddata_xml.childNodes:
            if load_curve.nodeType == load_curve.TEXT_NODE:
                continue
            id = load_curve.getAttribute("id")
            type = load_curve.getAttribute("type")
            lc = LoadCurve(id, type)
            lc.points = []
            for point in load_curve.childNodes:
                if point.nodeType == load_curve.TEXT_NODE:
                    continue
                xy = point.firstChild.nodeValue
                x_y = xy.split(",")
                lc.points.append(x_y)
            self.load_curves.append(lc)

        # Loads
        try:
            loads_xml = self.xml_document.getElementsByTagName("Loads")[0]
        except:
            loads_xml = None
        if loads_xml is not None:
            for load in loads_xml.getElementsByTagName("body_load"):
                x_xml = load.getElementsByTagName("x")[0]
                x = x_xml.firstChild.nodeValue
                x_curve = self.get_lc_by_id(int(x_xml.getAttribute("lc")))

                y_xml = load.getElementsByTagName("y")[0]
                y = y_xml.firstChild.nodeValue
                y_curve = self.get_lc_by_id(int(y_xml.getAttribute("lc")))

                z_xml = load.getElementsByTagName("z")[0]
                z = z_xml.firstChild.nodeValue
                z_curve = self.get_lc_by_id(int(z_xml.getAttribute("lc")))

                part = self.get_part_by_name(load.getAttribute("elem_set"))
                nload = Loads(x, y, z, part=part, x_curve=x_curve, y_curve=y_curve, z_curve=z_curve)
                self.loads.append(nload)

        # Output
        output_tag = self.xml_document.getElementsByTagName("Output")[0]

        plotfile_tag = output_tag.getElementsByTagName("plotfile")[0]
        plots = plotfile_tag.getElementsByTagName("var")
        for plot in plots:
            value = plot.getAttribute("type")
            self.plot_data.append(value)

        try:
            self.logged_node_data = self.xml_document.getElementsByTagName("node_data")[0].getAttribute("data").split(";")
        except:
            self.logged_node_data = []

        try:
            self.logged_tet_data = self.xml_document.getElementsByTagName("element_data")[0].getAttribute("data").split(";")
        except:
            self.logged_tet_data = []

    def get_node_by_id(self, id):
        return self.nodes[id - 1]

    def get_tet_by_id(self, id):
        return self.tets[id - 1]

    def get_mat_by_id(self, id):
        return self.materials[id - 1]

    def get_lc_by_id(self, id):
        return self.load_curves[id - 1]

    def get_grp_by_name(self, name):
        for group in self.groups:
            if group.name == name:
                return group

        return None

    def get_part_by_name(self, name):
        for part in self.parts:
            if part.name == name:
                return part

        return None



# A point data structure
class Point:
    def __init__(self, x, y, z, id):
        self.x = x
        self.y = y
        self.z = z
        self.idHou = id - 1
        self.idBio = id

    def __str__(self):
        return "Point {} with id {} at x: {} y: {} z: {}".format(self.idHou, self.idBio, self.x, self.y, self.z)


# A Tetrahedron data structure
class Tet:
    def __init__(self, v0, v1, v2, v3, id):
        self.v0 = v0
        self.v1 = v1
        self.v2 = v2
        self.v3 = v3
        self.idHou = id - 1
        self.idBio = id

    def __str__(self):
        return "Tetrahedron {} with id {} and vertecies from point id's [ {}, {}, {}, {} ]".format(self.idHou,
                                                                                                   self.idBio,
                                                                                                   self.v0,
                                                                                                   self.v1,
                                                                                                   self.v2,
                                                                                                   self.v3)

    @staticmethod
    def hou_pt_num(v):
        return v - 1


# A group data structure
class Group:
    def __init__(self, name, nodes):
        self.name = name
        self.nodes = nodes

    def __str__(self):
        return "Group {} with nodes {}".format(self.name, self.nodes)

class Part:
    def __init__(self, name, tets = [], material = None):
        self.name = name
        self.material = material
        self.tets = tets


# A material data structure
class Material:
    def __init__(self, id, name, dens, e, v, type="isotropic elastic"):
        self.id = id
        self.name = name
        self.dens = dens
        self.e = e
        self.v = v
        self.type = type


class Boundary:
    def __init__(self, group, type, params = {}, bc="x,y,z", curve=None):
        self.node_set = group.name
        self.bc = bc
        self.type = type
        self.params = params
        self.curve = curve


class LoadCurve:
    def __init__(self, id, type, points = []):
        self.id = id
        self.type = type
        self.points = points


class Loads:
    def __init__(self, x, y, z, type="const", part=None, x_curve=None, y_curve=None, z_curve=None):
        self.x = x
        self.y = y
        self.z = z
        self.type = type
        self.part = part
        self.x_curve = x_curve
        self.y_curve = y_curve
        self.z_curve = z_curve


# Convert .feb node strings into point objects
def node_to_point(node_text):
    sep_values = node_text.split(", ")

    values = []

    for value in sep_values:
        base_and_power = value.split('e')
        base = float(base_and_power[0])
        power = pow(10.0, float(base_and_power[1]))
        values.append(base * power)

    return values


# Convert .feb tet strings into tet objects
def elem_to_tet(tet_text):
    sep_values = tet_text.split(", ")

    values = []

    for value in sep_values:
        values.append(int(value))

    return values


# Convert point objects into .feb node strings
def point_to_node(point):
    xStr = '%.7e' % Decimal(str(point.x))
    yStr = '%.7e' % Decimal(str(point.y))
    zStr = '%.7e' % Decimal(str(point.z))
    return " {}, {}, {}".format(xStr, yStr, zStr)


# Convert tet objects into .feb tet strings
def tet_to_elem(tet):
    return " {}, {}, {}, {}".format(tet.v0, tet.v1, tet.v2, tet.v3)


# Convert material to Houdini Parm String
def mat_to_matParm(material):
    return"{};{};{};{};{};{}".format(material.id,
                                     material.name,
                                     material.type,
                                     material.dens,
                                     material.e,
                                     material.v)