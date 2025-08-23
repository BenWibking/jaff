import sys
import os

class Builder:
    def __init__(self, network):
        self.network = network

    def build(self, template="python_solve_ivp"):

        print("Building network with template:", template)

        # prepare the template path
        path_template = os.path.join(os.path.dirname(__file__), "templates", template)

        # prepare the build path
        path_build = os.path.join(os.path.dirname(__file__), "builds")

        # import module based on the template name
        try:
            module = __import__(f"jaff.plugins.{template}.plugin", fromlist=["main"])
        except ImportError as e:
            print(f"Error: Template '{template}' not found. Available templates are:")
            for template in os.listdir(os.path.join(os.path.dirname(__file__), "templates")):
                print(template)
            sys.exit(1)

        # call the main function of the module to preprocess the files
        # the definition of the main function is in the plugin folder
        module.main(self.network, path_template=path_template)

        print(f"Network built successfully using template '{template}'.")
        print(f"Output files are located in: {path_build}")
        
        return path_build