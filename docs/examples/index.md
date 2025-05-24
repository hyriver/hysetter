# Tutorials

The example notebooks have several additional dependencies that need to installed in
addition to `hysetter`. You can install all the dependencies using
[Pixi](https://pixi.sh/latest/). First, install Pixi and then run the following command
in the root of the repository:

```bash
pixi install -e dev
```

This will install all the dependencies needed to run the example notebooks in an
isolated environment under `./.pixi/envs/dev`. If you are using an IDE like
[VSCode](https://code.visualstudio.com/), it should automatically detect the
environment, so you can select it as the interpreter for the notebooks.

<div class="grid cards" markdown>

- [![HYMOD](images/hymod-flowchart.png){ loading=lazy }](hymod.ipynb "HYMOD") **HYMOD**
- [![NCRS-PDM](images/ncrspdm.png){ loading=lazy }](ncrspdm.ipynb "NCRS-PDM")
    **NCRS-PDM**

</div>
