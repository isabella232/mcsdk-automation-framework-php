import os
import shutil

from mcsdk.codebase import generator
from mcsdk.integration.os.process import Command


class CodeGenerator(generator.AbstractGenerator):
    """ Handles the Swagger codegen process but also custom generation processes """

    def _delete_standard_tests(self):
        """ The testing framework is also automated so we must delete the existing generated tests """
        api_tests_dir = os.path.join(self._repo_dir, 'test', 'Api')
        if os.path.isdir(api_tests_dir):
            shutil.rmtree(api_tests_dir)

        model_tests_dir = os.path.join(self._repo_dir, 'test', 'Model')
        if os.path.isdir(model_tests_dir):
            shutil.rmtree(model_tests_dir)

    def generate_sdk(self):
        """ Generates the SDK code using the swagger codegen library """
        cmd = " ".join([
            'java',
            '-jar',
            '{swagger_exec}'.format(swagger_exec=self._config['repos']['core']['swagger_cli']),
            'generate',
            '-l',
            'php',
            '-i',
            '{spec_file}'.format(spec_file=self._config['repos']['core']['swagger_spec']),
            '-t',
            '{templates_dir}'.format(templates_dir=os.path.join(self._templates_dir, 'mustache')),
            '-c',
            '{config_file}'.format(config_file=os.sep.join([self._config_dir, 'swagger-codegen-config.json'])),
            '-o',
            '{sdk_folder}'.format(sdk_folder=self._repo_dir)
        ])

        command = Command(cmd)
        command.run()

        return not command.returned_errors()

    def generate_client(self):
        """ Generates the SDK code custom PHP code generator """
        cmd = " ".join([
            'php',
            '-f',
            os.sep.join([self._root_dir, 'src', 'generator', self._config['generators']['php']]),
            os.path.join(self._templates_dir, 'phtml'),
            os.sep.join([self._config_dir, 'swagger-codegen-config.json']),
            self._repo_dir
        ])

        print("Generate PHP client command: " + cmd)

        command = Command(cmd)
        command.run()

        return not command.returned_errors()

    def generate(self):
        """ Generates the SDK code """
        self._delete_standard_tests()

        if self.generate_sdk() and self.generate_client():
            return 0

        return 255
