import math
import os


class Vector:
    """Class Vector in 3D space with x,y,z coordiantes and standard methods"""

    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z

    def __str__(self):
        return "[{},{},{}]".format(self.x, self.y, self.z)

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, other):
        if type(other) == float or type(other) == int:
            return Vector(self.x * other, self.y * other, self.z * other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        if type(other) == float or type(other) == int:
            return Vector(self.x / other, self.y / other, self.z / other)

    def dot(self, other):
        # returns dot product of 2 vectors
        if type(other) == type(self):
            return self.x * other.x + self.y * other.y + self.z * other.z

    def magnitude(self):
        # returns magnitude of the vector
        return math.sqrt(
            math.pow(self.x, 2) + math.pow(self.y, 2) + math.pow(self.z, 2)
        )

    def normalise(self):
        # returns unit vector in the same dir as the current vector
        m = self.magnitude()
        return Vector(x=self.x / m, y=self.y / m, z=self.z / m)


class Point:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z

    def __str__(self):
        return "[{},{},{}]".format(self.x, self.y, self.z)

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, other):
        if type(other) == type(Point()):
            return Point(self.x * other.x, self.y * other.y, self.z * other.z)

    def __truediv__(self, other):
        if type(other) == type(Point()):
            return Point(self.x / other, self.y / other, self.z / other)


class Colour:
    def __init__(self, r=0, g=0, b=0, max=255, hex=""):
        self.r = r
        self.g = g
        self.b = b
        self.max = max
        self.hex = hex

    def __mul__(self, other):
        return Colour(
            min(self.r * other, 1), min(self.g * other, 1), min(self.b * other, 1)
        )

    def __rmul__(self, other):
        return self.__mul__(other)

    def __add__(self, other):
        if type(other) == type(Colour()):
            return Colour(
                min(self.r + other.r, 1),
                min(self.g + other.g, 1),
                min(self.b + other.b, 1),
            )

    def from_hex(self):
        r = int(self.hex[1:3], 16) / 255
        g = int(self.hex[3:5], 16) / 255
        b = int(self.hex[5:7], 16) / 255
        return Colour(r, g, b)

    def __abs__(self):
        return Colour(abs(self.r), abs(self.g), abs(self.b))

    def __str__(self):
        return "{},{},{}".format(self.r, self.g, self.b)

    def normalise(self):
        return Colour(
            int(self.r * self.max), int(self.g * self.max), int(self.b * self.max)
        )


class PPM:
    upper = 255
    red = Colour(1, 0, 0)
    green = Colour(0, 1, 0)
    blue = Colour(0, 0, 1)

    def __init__(self, W=0, H=0, arr=[], name="def"):
        self.W = W
        self.H = H
        self.name = name
        self.arr = arr or [
            [Colour(max=self.upper).normalise() for _ in range(W)] for _ in range(H)
        ]

    def set_pixel(self, x, y, col=Colour()):
        self.arr[y][x] = col

    def save(self):
        content = list()
        header = "P3\n{} {}\n {}\n".format(self.W, self.H, self.upper)
        content.append(header)
        pix_arr = self.arr
        for y in range(self.H):
            cur_y = ""
            for x in range(self.W):
                cur_y += "{} {} {} ".format(
                    pix_arr[y][x].r, pix_arr[y][x].g, pix_arr[y][x].b
                )
            cur_y += "\n"
            content.append(cur_y)

        with open("{}.ppm".format(self.name), "w") as file:
            file.writelines(content)


class Sphere:
    def __init__(
        self,
        pos=Point(0, 0, 0),
        rad=0.5,
        col=Colour(1, 1, 1),
        ambient=0.05,
        diffuse=1.0,
        specular=1.0,
    ):
        self.pos = pos
        self.rad = rad
        self.col = col
        self.ambient = ambient
        self.diffuse = diffuse
        self.specular = specular


class Light:
    def __init__(self, pos=Point(0, 0, 0), col=Colour(1, 1, 1)):
        self.col = col
        self.pos = pos


class RayRender:
    def __init__(
        self,
        W,
        H,
        objects=[],
        cam_pos=Point(0, 0, -1),
        lights=[Light(Point(1, 1, -1), Colour(1, 1, 1))],
        specular_k=50,
    ):
        self.W = W
        self.H = H
        self.aspect_ratio = float(self.W) / self.H
        self.x_min = -1
        self.y_min = -1 / self.aspect_ratio
        self.d_y = (-self.y_min * 2) / (self.H - 1)
        self.d_x = 2 / (self.W - 1)
        self.cam_pos = cam_pos
        self.objects = objects
        self.lights = lights
        self.specular_k = specular_k

    def if_intersect(self, a, b, c):
        discriminant = pow(b, 2) - 4 * a * c
        # we only use negative sign for discriminant due to the assumption that cam_pos is in negative z
        d = -(-b - pow(discriminant, 0.5)) / (2 * a)
        return (discriminant >= 0 and d >= 0), d

    def normal(self, surface_point, center):
        return (surface_point - center).normalise()

    def lambert_shading(self, v_light, v_norm, m_coef):
        return max(-v_norm.normalise().dot(v_light.normalise()) * m_coef, 0)

    def phong_shading(self, v_viewer, v_reflected, v_norm, shininess):
        v_half = v_viewer + v_reflected
        v_half = v_half.normalise()
        return pow(max(-v_half.dot(v_norm.normalise()), 0), self.specular_k) * shininess

    def color_at(self, col, object, light, v_normal, v_viewer, v_light):
        col += object.col * self.lambert_shading(v_light, v_normal, object.diffuse)
        col += light.col * self.phong_shading(
            v_viewer, v_light, v_normal, object.specular
        )
        return col

    def ray_tracing(self):
        plot = PPM(self.W, self.H)
        for object in objects:
            sphere_to_ray = object.pos - self.cam_pos
            for y in range(self.H):
                y0 = self.y_min + (self.d_y * y)
                for x in range(self.W):
                    x0 = self.x_min + (self.d_x * x)
                    ray_dir = Vector(
                        x0 - self.cam_pos.x,
                        y0 - self.cam_pos.y,
                        object.pos.z - self.cam_pos.z,
                    ).normalise()

                    a = 1
                    b = 2 * ray_dir.dot(sphere_to_ray)
                    c = sphere_to_ray.dot(sphere_to_ray) - pow(object.rad, 2)
                    intersect, d = self.if_intersect(a, b, c)

                    if intersect:
                        hit_pos = self.cam_pos + (ray_dir) * d
                        hit_pos = Point(hit_pos.x, hit_pos.y, hit_pos.z)

                        v_normal = self.normal(hit_pos, object.pos)
                        v_viewer = self.cam_pos - hit_pos
                        observed_col = Colour(
                            object.ambient, object.ambient, object.ambient
                        )
                        for light in self.lights:
                            v_light = light.pos - hit_pos
                            observed_col += self.color_at(
                                observed_col, object, light, v_normal, v_viewer, v_light
                            )
                            # print(observed_col)
                        observed_col = abs(observed_col.normalise())
                        plot.set_pixel(x, y, observed_col)
        plot.save()


print(os.getcwd())
WIDTH = 200
HEIGHT = 200
cam_pos = Point(0, 0, -1)
lights = [
    Light(Point(1, 1.5, -1), Colour(hex="#ffffff").from_hex()),
    Light(Point(0, 33, 33), Colour(hex="#00ff00").from_hex()),
]
objects = [
    Sphere(
        pos=Point(0, 0, 0),
        rad=0.3,
        col=Colour(hex="#00ff00").from_hex(),
        ambient=0.07,
        diffuse=0.6,
        specular=0.9,
    ),
    Sphere(
        pos=Point(-0.4, -0.2, 0),
        rad=0.3,
        col=Colour(hex="#ff00ff").from_hex(),
        ambient=0.07,
        diffuse=0.6,
        specular=0.9,
    ),
    Sphere(
        pos=Point(0.4, -0.2, 0),
        rad=0.3,
        col=Colour(hex="#101010").from_hex(),
        ambient=0.2,
        diffuse=0.4,
        specular=0.9,
    ),
]
ppm = RayRender(WIDTH, HEIGHT, objects, cam_pos, lights)
ppm.ray_tracing()
