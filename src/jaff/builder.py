import sys
import os

class Builder:
    def __init__(self, network):
        self.network = network

    def build(self, template="python_solve_ivp"):

        print("Building network with template:", template)

        # import module based on the template name
        try:
            module = __import__(f"jaff.plugins.{template}.plugin", fromlist=["main"])
        except ImportError as e:
            print(f"Error: Template '{template}' not found. Available templates: python_solve_ivp")
            sys.exit(1)

        path_template = os.path.join(os.path.dirname(__file__), "templates", template)
        module.main(self.network, path_template=path_template)