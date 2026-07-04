from pmpge.graphics import ImageResource, GraphicsDrawImageTrait


class DrawImage(GraphicsDrawImageTrait):
    """
    DrawImage draws an image at the specified position. By default the image is drawn
    centered on the position (centered according to the same specification as a sprites
    image). Optionally, this can be drawn using the x, y position as the top left corner
    by setting centered = False.

    The DrawImage trait requires a Position trait to be present on the GameObject.

    The DrawImage trait requires a graphics specific implementation called
    GraphicsDrawImageTrait which does the actual drawing (and therefore needs to
    provide at least a `draw()`) method. It should use the `offset_x` and `offset_y`
    properties (which are placed on `image`) to adjust the position of the drawn
    image relative to the GameObjects x and y position.
    """
    x: int
    y: int

    # The width and height properties are required for Sprites but useful generally
    width: int
    height: int

    image: ImageResource

    def __init__(self, image: str, centered: bool = True,
                 hint_requires_transparency: bool = True):
        """
        Creates the DrawImage trait using the given image resource name.

        When used with Sprites, the `centered` parameter should be `True`.

        The `hint_requires_transparency` parameter in the constructor is passed to
        the ImageResource to allow for driver specific optimisations. Set this to
        `False` if your image does not need transparency as it has a positive impact
        on performance on microcontrollers. It makes no difference with Pygame Zero.
        """
        GraphicsDrawImageTrait.__init__(self)

        # FUTURE: We could extract ImageResource to be passed in.
        image = ImageResource(image, hint_requires_transparency=hint_requires_transparency)
        image.centered = centered

        self.image = image
        self.width = image.width
        self.height = image.height

        if image.centered:
            image.offset_x = image.width // 2
            image.offset_y = image.height // 2
        else:
            image.offset_x = 0
            image.offset_y = 0

    def merged(self):
        """
        Hooks the Sprite we have just been attached to into the ImageResource
        notify event to keep the width and height in sync with any new image
        loaded.
        """

        def on_notify():
            image = self.image
            width, height = image.width, image.height
            self.width = width
            self.height = height

            if image.centered:
                image.offset_x = width // 2
                image.offset_y = height // 2
            else:
                image.offset_x = 0
                image.offset_y = 0

        self.image.notify = on_notify
