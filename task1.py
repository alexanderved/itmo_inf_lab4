import xml.etree.ElementTree as xml
import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    print('Import error')
    from yaml import Loader


def create_xml_element(k, v):
    element = xml.Element(k)
    if type(v) is list or type(v) is dict:
        element.extend(create_xml_elements(v))
    else:
        element.text = str(v)

    return element


def create_xml_elements(data):
    if type(data) is list:
        return [create_xml_element('value', v) for v in data]
    elif type(data) is dict:
        return [create_xml_element(k, v) for k, v in data.items()]
    else:
        print('Unknown type of data')
        exit(1)


def dump_xml(data):
    root = create_xml_element('root', data)

    tree = xml.ElementTree(root)
    xml.indent(tree, space='    ', level=0)

    return tree


def main():
    with open('input/timetable.yaml', 'r') as in_file:
        data = yaml.load(in_file.read(), Loader=Loader)

        dump_xml(data).write('output/task1.xml', encoding='UTF-8', xml_declaration=True)


if __name__ == '__main__':
    main()