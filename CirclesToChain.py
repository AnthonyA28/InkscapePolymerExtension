
from inkex import * 
import inkex
from lxml import etree
import xml.etree.ElementTree as ET
import numpy as np 
import random
import os, sys
import math
import re





def inkscape_path_to_points(svg_content, l):
    
    points = []
    
    segments = re.findall(r'([A-Za-z]|-?[0-9.]+)\s*', svg_content)
    i = 0
    last_point = (0.0, 0.0)
    
    while i < len(segments):
        segment = segments[i]

        if segment in ['M', 'm', 'L', 'l']:
            dx = float(segments[i + 1])
            dy = float(segments[i + 2])

            if segment.islower():
                x = last_point[0] + dx
                y = last_point[1] + dy
            else:
                x = dx
                y = dy

            points.append((x, y))
            last_point = (x, y)
            i += 3

        elif segment in ['H', 'h']:
            dx = float(segments[i + 1])

            if segment.islower():
                x = last_point[0] + dx
                y = last_point[1]
            else:
                x = dx
                y = last_point[1]

            points.append((x, y))
            last_point = (x, y)
            i += 2

        elif segment in ['V', 'v']:
            dy = float(segments[i + 1])

            if segment.islower():
                x = last_point[0]
                y = last_point[1] + dy
            else:
                x = last_point[0]
                y = dy

            points.append((x, y))
            last_point = (x, y)
            i += 2

        elif segment in ['C', 'c']:
            x1 = float(segments[i + 1])
            y1 = float(segments[i + 2])
            x2 = float(segments[i + 3])
            y2 = float(segments[i + 4])
            x = float(segments[i + 5])
            y = float(segments[i + 6])

            if segment.islower():
                x1 += last_point[0]
                y1 += last_point[1]
                x2 += last_point[0]
                y2 += last_point[1]
                x += last_point[0]
                y += last_point[1]

            # Calculate the actual length of the Bezier curve
            length = math.hypot(x - last_point[0], y - last_point[1])

            # Calculate the number of points required based on the desired distance 'l'
            num_points = max(int(length / l), 1)

            # Calculate the parameter increment
            t_increment = 1.0 / num_points

            # Calculate and add the points along the curve
            for j in range(1, num_points + 1):
                t = j * t_increment
                x_point = (1 - t) ** 3 * last_point[0] + 3 * (1 - t) ** 2 * t * x1 + 3 * (1 - t) * t ** 2 * x2 + t ** 3 * x
                y_point = (1 - t) ** 3 * last_point[1] + 3 * (1 - t) ** 2 * t * y1 + 3 * (1 - t) * t ** 2 * y2 + t ** 3 * y
                points.append((x_point, y_point))

            last_point = (x, y)
            i += 7
            
        else:
            i += 1


    return points




def remove_close_points(points, l):
    new_points = []
    new_points.append(points[0])
    i = 1
    j = 0 
    while i < len(points):
        x1, y1 = points[j]
        x2, y2 = points[i]
        distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        if distance >= l:
            new_points.append(points[i])
            j = i 
        i += 1

    return new_points




class Chains(inkex.EffectExtension):

    def __init__(self):
        inkex.Effect.__init__(self)
        # inkex.utils.debug(self.options)

    def add_arguments(self, pars):
        
        pars.add_argument("--CircleRadius", type=float, default="8", help="radius of circles")
        pars.add_argument("--DistBetweenCircles", type=float, default="8", help="the distance between consecutive circles")
        pars.add_argument("--CircleStrokeWidth", type=float, default="8", help="stroke width of circles")
        pars.add_argument("--CircleRadiusVariation", type=float, default="0", help="the variation in the radius")
        pars.add_argument("--wavelen", type=float, default="8", help="the distance the radius variation occurs")
        pars.add_argument("--FillColor",   type=inkex.colors.Color, help="fill color of circles")
        pars.add_argument("--StrokeColor", type=inkex.colors.Color, help="stroke color of circles")

        pars.add_argument("--tab", help="The selected UI-tab when OK was pressed")

        

    def effect(self):

        
        svg = self.document.getroot()

        p_list = []

        selected_shapes = []

        for node in svg.selection.rendering_order():
            selected_shapes.append(node)

        for node in selected_shapes:


            chainGroup = Group()
            str_node = node.get("d")
            points = inkscape_path_to_points(str_node, self.options.DistBetweenCircles/100)
            new_points = remove_close_points(points, self.options.DistBetweenCircles)

            total_distance =0 
            for i in range(0, len(new_points)):
                
                if ( i > 0 ):
                    x1 = new_points[i-1][0]
                    y1 = new_points[i-1][1]
                    x2 = new_points[i][0]
                    y2 = new_points[i][1]
                    distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                else:
                    distance = 0 
                total_distance += distance
                
                dR = self.options.CircleRadiusVariation*np.cos(total_distance*2*3.14/self.options.wavelen)

                p = new_points[i]
                circle = etree.Element(inkex.addNS('circle', 'svg'))
                circle.set('cx', str(p[0]))
                circle.set('cy', str(p[1]))
                circle.set('stroke-width', str(self.options.CircleStrokeWidth))
                circle.set('r', str(self.options.CircleRadius+dR))
                circle.set('fill', str(self.options.FillColor))
                circle.set('stroke', str(self.options.StrokeColor))
                svg.append(circle)


                
                chainGroup.set('id', str("ChainUnits_" + str(random.randint(10000, 100000))) )
                chainGroup.append(circle)
                svg.append(chainGroup)


if __name__ == "__main__":
    effect = Chains()
    effect.run()
