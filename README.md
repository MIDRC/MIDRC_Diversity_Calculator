                  
 
<h1 align="center" style="font-weight: bold;">MIDRC Diversity Calculator</h1>

<p align="center">
<a href="#tech">Technologies</a>
<a href="#started">Getting Started</a>
<a href="#colab">Collaborators</a>
<a href="#contribute">Contribute</a> 
</p>


<p align="center">Diversity calculator for comparing representativeness of biomedical data</p>


<p align="center">
<a href="https://www.midrc.org/">📱 Visit MIDRC Website</a>
</p>
 
<h2 id="technologies">💻 Technologies</h2>

Technologies used with this application
* Python
* PySide6
* numpy
* scipy
* pandas

There is a requirements.txt file available to install requirements
 
<h2 id="started">🚀 Getting started</h2>

#### Configure yaml
First, configure your own jsdconfig.yaml file to load default data. There is a jsdconfig-example.yaml file provided that may be copied over or used as a template for your own config file.
* The filename needs to be specified, and a human-readable name should be provided for use in the plots and figures. 
* There is a 'remove column name text' option that is used for MIDRC data sources

#### Run application
To start the application, run `python main.py`

#### Generating plots and figures
* Select the files you wish to compare in the drop-down menus that you wish to make comparisons between. 
* A checkbox is provided next to the drop-down menus to select whether additional plots should be shown for each individual file selected. 
* Note: displaying plots for two or more files simultaneously may require a 4k monitor

#### Generating custom excel files
Use the provided MIDRC, CDC, and Census excel files as an example on how to prepare your custom data. For each date, cumulative sums are expected. Each attribute should have its own excel worksheet which will be parsed by the application. Column names within the worksheet are also parsed (a date column is expected) and where there is a matching column name within a worksheet of the same name, the JSD will be calculated using those values. The list of attributes provided in the GUI should be a list where worksheets with an identical name exist in both files.

#### GUI Manipulation
The plots and figures should be movable, better defaults for the UI are still a work-in-progress. 

To see the list of available dock widgets, you can right-click on any menu/title bar area, i.e. either the main window menu bar or any title bar in a dock widget.

Keyboard commands can be used to copy and paste the calculated JSD values (and dates) and pasted in Excel or a notebook as tab-delimited data.

 
<h3>Prerequisites</h3>

- Python 3.9 or highter
- [Git](https://github.com)
 
<h3>Cloning</h3>

How to clone your project

```bash
git clone https://github.com/MIDRC/MIDRC_Diversity_Calculator.git
```
 
<h3>Starting</h3>

How to start the project

```bash
cd MIDRC_Diversity_Calculator
cp jsdconfig-example.yaml jsdconfig.yaml
python main.py
```
 
<h2 id="colab">🤝 Collaborators</h2>

<p>Special thank you for all people that contributed for this project.</p>
<table>
<tr>

<td align="center">
<a href="https://github.com/rtomek">
<img src="https://avatars.githubusercontent.com/u/47761173" width="100px;" alt="Robert Tomek Profile Picture"/><br>
<sub>
<b>Robert Tomek</b>
</sub>
</a>
</td>

</tr>
</table>
 
<h2 id="contribute">📫 Contribute</h2>

1. `git clone https://github.com/MIDRC/MIDRC_Diversity_Calculator.git`
2. `git checkout -b feature/NAME`
3. Open a Pull Request explaining the problem solved or feature made, if exists, append screenshot of visual modifications and wait for the review!
 
<h3>Documentations that might help</h3>

[📝 How to create a Pull Request](https://www.atlassian.com/br/git/tutorials/making-a-pull-request)
