import os
from handmade.conf import settings
from handmade.exceptions import ProgrammingError, ResourceError
from handmade.plugins import Plugin


class BaseResource(object):
    def get(self, *args, **kwargs):
        raise NotImplementedError()

    def validate(self, *args, **kwargs):
        raise NotImplementedError()

    def process(self, *args, **kwargs):
        raise NotImplementedError()

    @classmethod
    def default_value(cls, value):
        raise NotImplementedError()

    def __init__(self, plugin=None, *args, **kwargs):
        if not plugin:
            raise ProgrammingError("Plugin is not set while creating a resource. "
                                   "You should register resources with the manager")
        self.plugin = plugin
        self.validate()


class FileResource(BaseResource):
    class FileNotFound(ResourceError):
        pass

    def __init__(self, filename, *args, **kwargs):
        self.filename = filename
        self.source_path = None
        self.destination_path = None
        super(FileResource, self).__init__(*args, **kwargs)

    def get(self, *args, **kwargs):
        return self.destination_path

    @classmethod
    def default_value(cls, value):
        return {
            "filename": value
        }

    def build_destination_path(self):
        chunks = [settings.RESOURCES_ROOT]
        chunks += self.plugin.split(".")
        chunks.append(self.filename)
        full_path = os.path.join(*chunks)
        if not os.path.exists(os.path.dirname(full_path)):
            os.makedirs(os.path.dirname(full_path))
        self.destination_path = full_path

    def process(self, *args, **kwargs):
        self.build_destination_path()
        import shutil
        shutil.copy(self.source_path, self.destination_path)

    def validate(self, *args, **kwargs):
        plugin_path = Plugin.get_plugin_path(self.plugin)

        full_path = os.path.join(plugin_path, 'data', self.filename)
        if not os.path.exists(full_path):
            raise FileResource.FileNotFound("File %s not found. "
                                            "File name should be relative to plugin's data directory" % self.filename)
        else:
            self.source_path = full_path


class ImageResource(FileResource):
    pass


class AtlasResource(FileResource):
    DEFAULT_SIZE = (1024, 1024)

    def process(self, *args, **kwargs):
        self.build_destination_path()

        from kivy.atlas import Atlas
        self.atlas_filename, self.atlas_meta = Atlas.create(
            outname=self.destination_path,
            filenames=self.source_files,
            size=self.size,
            **kwargs
        )

    class NotADirectory(ResourceError):
        pass

    class DirectoryEmpty(ResourceError):
        pass

    def validate(self, *args, **kwargs):
        super(AtlasResource, self).validate(*args, **kwargs)
        if not os.path.isdir(self.source_path):
            raise AtlasResource.NotADirectory("Atlas filename should be a directory, "
                                              "%s is not a directory" % self.source_path)

        import glob
        self.source_files = [os.path.join(self.source_path, filename)
                             for filename in glob.glob1(self.source_path, "*.png")]

        if not self.source_files:
            raise AtlasResource.DirectoryEmpty("Atlas directory %s does not contain png files" % self.source_path)

    def __init__(self, filename, size=None, *args, **kwargs):
        self.source_files = None
        super(AtlasResource, self).__init__(filename, *args, **kwargs)
        self.size = size or self.DEFAULT_SIZE

        self.atlas_filename = None
        self.atlas_meta = None
