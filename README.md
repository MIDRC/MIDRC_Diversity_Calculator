# MIDRC-REACT Representativeness Exploration and Comparison Tool

[Technologies](#technologies) | [Getting Started](#getting-started) | [Collaborators](#collaborators) | [References](#references) | [Contribute](#contribute)

[📱 Visit MIDRC Website](https://www.midrc.org/)

## :information_source: Overview

The MIDRC Representativeness Exploration and Comparison Tool (REACT) is a tool designed to compare the representativeness of biomedical data. By leveraging the Jensen‑Shannon distance (JSD) measure, it provides insight into the demographic representativeness of datasets within the biomedical field. It also supports monitoring historical data for changes in representativeness. Developed by MIDRC, it assesses how well data within the open data commons represent the US population and can be adapted for other data needs.

## :wrench: Features

- **Jensen‑Shannon Distance Calculation**: Uses the JSD measure to assess data representativeness.
- **Comparative Analysis**: Enables comparisons between various datasets.
- **Biomedical Focus**: Tailored for biomedical data analysis.
- **Historical Data**: Supports monitoring changes over time.

## :notebook_with_decorative_cover: Background

The methodology is based on the 2023 paper by Whitney et al. titled [“Longitudinal assessment of demographic representativeness in the Medical Imaging and Data Resource Center open data commons”\[1\]](#1). This paper provides the theoretical approach for using JSD.

![screenshot](docs/images/screenshot.jpg)

## Technologies

**Technologies used with this application:**
- Python
- PySide6
- numpy, scipy, pandas

A `requirements.txt` file is provided for installing dependencies.

## Getting Started

### Configure YAML

First, create your own `jsdconfig.yaml` file to select which data to load by default using the provided example file:

- Ensure the filename is correctly specified and include a human‑readable name for display in plots.
- See the *Generating custom Excel files* section for details.
- Run the following command to copy the example configuration:

  ```bash
  cp jsdconfig-example.yaml jsdconfig.yaml
  ```

### Run Application

To start the application within the project directory, run:

  ```bash
  pip install -e .
  midrc-react
  ```

### Generating Plots and Figures

* Use the drop‑down menus to select files for comparison.
* A checkbox is provided next to each drop‑down to display individual plots.
*  Note: Displaying multiple files simultaneously may require a 4k monitor.

### Generating Custom Excel Files

* Use the MIDRC, CDC, and Census Excel files as examples.
* For each date, ***cumulative sums are expected***.
* **Each attribute should have its own sheet** so it is automatically parsed.
* Where matching column names exist across sheets, JSD is calculated.
* ***A Date column is required*** and should be sorted. Please see how the census data is loaded using the example config file if your data does not have multiple dates.
* The `remove column name text` parameter adjusts for `(CUSUM)` suffixes in the MIDRC-generated data, and is optional.

### Layout and Loading of CSV/TSV Files

The application supports CSV/TSV files as well as Excel:
* CSV files use comma\-separation; TSV files use tabs.
* The file options dialog adjusts based on file type.
* ***Multi\-Dimensional Distances:*** The usage of multi-dimensional distances (FAMD, Aggregate) requires the full data in CSV or TSV format rather than just cumulative sums..
* **File\-specific Persistence:** Saves settings for each file.
* **Default Fallback:** Loads the last used settings if no file data is found.
* **Column Selection:** The dialog allows selecting which columns will be used in the display, and all columns selected are used for the multi-dimensional distances.
* **Numeric Column Selection:** You may set which columns are numerical instead of categorical, as well as setting how to bin the data for categorical distances. The GUI provides options for a range of values for the bins, and you may adjust the binning by editing the YAML content provided after creating the default bins.

The application can load TSV files downloaded directly from data.midrc.org or via the gen3 interface to MIDRC using the plugin included in the plugins directory.

### GUI Manipulation

* Plots and figures are movable, resizable, or can be hidden.
* Right‑click on any menu or title-bar area to view available dock widgets.
* Keyboard shortcuts allow copying JSD values and dates as tab‑delimited data for Excel or notebooks.

### Prerequisites

* Python 3.10 or higher
* [Git](https://github.com)

### Cloning

Clone the repository:

```bash
git clone https://github.com/MIDRC/MIDRC-REACT.git
```

Enter the project directory:

```bash
cd MIDRC-REACT
```

### Installing Requirements

Install dependencies using pip:

```bash
python -m pip install --upgrade pip
pip install -r midrc_react/requirements.txt
```

### Starting

Start the project using:

```bash
cp jsdconfig-example.yaml jsdconfig.yaml
pip install -e .
midrc-react
```

Once installed using `pip install -e .` from the base directory, you may run the application from any directory using:

`midrc-react`

or, alternatively:
`MIDRC-REACT`

## 🤝 Collaborators

### Special Thanks

Robert Tomek, Maryellen Giger, Heather Whitney

#### Acknowledgements

Natalie Baughan, Kyle Myers, Karen Drukker, Judy Gichoya, Brad Bower, Weijie Chen, Nicholas Gruszauskas, Jayashree Kalpathy\-Cramer, Sanmi Koyejo, Rui Sá, Berkman Sahiner, Zi Zhang

**MIDRC AI Reliability Working Group:**

* *Co\-leads:* Karen Drukker, Judy Wawira Gichoya
* *AAPM:* Weijie Chen, Kyle Myers, Heather Whitney
* *ACR:* Jayashree Kalpathy\-Cramer
* *RSNA:* Zi Jill Zhang
* *NIH:* Rui Sá, Brad Bower
* *MIDRC Central (University of Chicago):* Maryellen Giger, Nick Gruszauskas, Katie Pizer, Robert Tomek
* *Project Manager:* Emily Townley

## :book: References

<a id="1">[1]</a> Whitney HM, Baughan N, Myers KJ, Drukker K, Gichoya J, Bower B, Chen W, Gruszauskas N, Kalpathy\-Cramer J, Koyejo S, Sá RC, Sahiner B, Zhang Z, Giger ML.
*Longitudinal assessment of demographic representativeness in the Medical Imaging and Data Resource Center open data commons.*
J Med Imaging (Bellingham). 2023 Nov;10(6):61105.
[doi: 10.1117/1.JMI.10.6.061105](https://doi.org/10.1117/1.JMI.10.6.061105). Epub 2023 Jul 18. PMID: 37469387; PMCID: PMC10353566.

## 📫 Contribute

1. Clone the repository:

```bash
git clone https://github.com/MIDRC/MIDRC_Diversity_Calculator.git
```

2. Create a feature branch:

`git checkout -b feature/NAME`

3. Open a Pull Request explaining the changes, and attach any necessary screenshots.

### Documentation That Might Help

[📝 How to create a Pull Request](https://www.atlassian.com/br/git/tutorials/making-a-pull-request)

## :heavy_check_mark: License

This project is licensed under the Apache 2.0 license. See the `LICENSE` file for details.

## Acknowledgement

*This work was supported in part by The Medical Imaging and Data Resource Center (MIDRC), funded by the National Institute of Biomedical Imaging and Bioengineering (NIBIB) and through ARPA\-H.*