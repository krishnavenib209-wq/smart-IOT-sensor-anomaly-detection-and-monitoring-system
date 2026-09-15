\# SmartHome-IoT-Federated-Anomaly-Dataset



\## 📌 Overview

This repository provides a real-world heterogeneous smart-home IoT dataset designed for anomaly detection under both centralized machine learning (ML) and federated learning (FL) paradigms.



The dataset was collected from a residential deployment consisting of four Raspberry Pi devices (Pi-4 to Pi-7), each equipped with different sensor configurations. It captures realistic IoT conditions, including device heterogeneity, temporal irregularities, and naturally imbalanced anomaly distributions.



An integrity-aware curation pipeline was applied to ensure data quality, transparency, and reproducibility.



\---



\## 🧱 Repository Structure

SmartHome-IoT-Federated-Anomaly-Dataset/

│

├── data/

│ ├── merged/

│ │ └── dataset\_curated.csv

│ └── clients\_full/

│ ├── pi4.csv

│ ├── pi5.csv

│ ├── pi6.csv

│ └── pi7.csv

│

├── experiments/

│ ├── ml\_subset.csv

│ ├── ml\_subset\_summary.csv

│ ├── fl\_clients\_sampled/

│ │ ├── pi4\_sample.csv

│ │ ├── pi5\_sample.csv

│ │ ├── pi6\_sample.csv

│ │ └── pi7\_sample.csv

│ ├── fl\_clients\_sampled\_summary.csv

│ └── sampling\_notes.txt

│

├── analysis/

│ └── dataset\_audit/

│

├── supplementary/

│ ├── raw/

│ ├── logs/

│ └── final\_freeze/

│

├── scripts/

│

└── README.md



\---



\## 📊 Dataset Summary



\- Total records (curated): \*\*7,005,585\*\*

\- Devices: \*\*4 Raspberry Pi nodes\*\*

\- Sampling interval: \~2–2.5 seconds

\- Data type: Multivariate time-series



\### Sensor Configuration



| Device | Sensors | Features |

|--------|--------|----------|

| Pi-4 | DHT22, PIR | temperature, humidity, motion |

| Pi-5 | DHT22, ADXL345 | temperature, humidity, acceleration |

| Pi-6 | DHT22, PIR | temperature, humidity, motion |

| Pi-7 | DHT22, MQ gas sensor | temperature, humidity, gas concentration |



\---
## 🧠 Dataset Description

This dataset consists of multivariate time-series sensor data collected from a real-world smart-home IoT deployment involving four Raspberry Pi devices. Each device is equipped with heterogeneous sensors, capturing environmental, motion, and system-level observations.

The dataset is designed to support anomaly detection research under both centralized and federated learning paradigms, preserving real-world characteristics such as device heterogeneity, temporal irregularities, and imbalanced anomaly distributions.
## 🧩 Data Format

Each CSV file contains timestamped sensor readings with the following structure:

- `timestamp` – ISO-8601 formatted datetime
- `temperature_C` – Temperature in Celsius
- `humidity` – Relative humidity (%)
- `pir_motion` – Binary motion detection (0/1)
- `accel_x_m_s2`, `accel_y_m_s2`, `accel_z_m_s2` – Accelerometer readings (m/s²)
- `mq_raw` – Raw gas sensor signal
- `mq_gas_detected` – Binary gas detection flag
- `anomaly_flag` – Binary anomaly indicator (0/1)
- `anomaly_type` – Type of anomaly
- `anomaly_source` – Source of anomaly (e.g., injected, clean)

Note: Not all features are present for every device due to heterogeneous sensor configurations.
---
## ⚠️ Data Characteristics

- Highly imbalanced anomaly distribution (~0.6% anomalies)
- Non-IID data across devices
- Heterogeneous feature spaces per device
- Temporal gaps and irregularities
- Real-world noise and sensor inconsistencies
---
## 🔬 Reproducibility

All preprocessing, validation, and dataset construction steps are fully reproducible using the scripts provided in the `scripts/` directory.

Audit outputs, intermediate statistics, and validation reports are included to ensure transparency and traceability of the dataset curation process.

---
## ⚠️ Limitations

- Limited to four devices in a single smart-home environment
- Some anomalies are artificially injected to simulate rare events
- Feature availability differs across devices due to hardware configuration
---
## 📜 Acknowledgment

This dataset was collected and curated as part of ongoing research in federated learning and lightweight security for IoT systems.
---
\## ⚙️ Data Curation Pipeline

The dataset was processed using an integrity-aware pipeline including:



\- Timestamp parsing and ISO-8601 normalization  

\- Detection and correction of malformed timestamps  

\- Removal of irreparable records (\~0.53%)  

\- Duplicate removal (\~0.8%)  

\- Anomaly label validation and normalization  

\- Dataset auditing and traceability logging  



Detailed outputs are available in:

analysis/dataset\_audit/

\---



\## 🔗 Federated Learning Support



The dataset is inherently suitable for federated learning:



\- Each Raspberry Pi corresponds to a \*\*federated client\*\*

\- Device-level partitions are provided in:

data/clients\_full/



\### Key Characteristics



\- Non-IID data distribution  

\- Heterogeneous feature spaces  

\- Device-specific anomaly behavior  



\---



\## 🧪 Experimental Subsets



To support reproducibility:

experiments/



contains:

\- A \*\*1 million record centralized subset\*\*

\- Corresponding \*\*federated client partitions\*\*

\- Sampling summaries and documentation  

\---

\## 🔍 Dataset Audit


Comprehensive audit outputs are included:

\- Timestamp validation reports  

\- Label integrity checks  

\- Feature statistics  

\- Device-level summaries  

Location:

analysis/dataset\_audit/

\---

## 📦 Supplementary Data

The `supplementary/` directory provides additional resources to ensure transparency, traceability, and reproducibility.

Includes:

- **Raw sensor logs** (`supplementary/raw/`)  
  Original, unmodified data collected from each Raspberry Pi device.

- **Retroactive anomaly scenarios** (`supplementary/retro_anomalies/`)  
  Anomaly events injected post hoc into selected time periods (e.g., holiday intervals) to simulate realistic fault conditions.  
  These files are derived from the original raw logs and are provided to support controlled experimentation and reproducibility.

- **System and collection logs** (`supplementary/logs/`, optional)  
  Logs related to data acquisition and system monitoring.

- **Final dataset freeze** (`supplementary/final_freeze/`)  
  Includes:
  - File manifest
  - SHA-256 hash verification for dataset integrity

\## 🧾 Scripts

The `scripts/` directory contains utilities for:

\- Dataset curation  

\- Timestamp repair  

\- Dataset validation  

\- Client partitioning  

\---

\## 📌 Usage


\### Centralized Learning

data/merged/dataset\_curated.csv

\### Federated Learning

data/clients\_full/

\---

## 📖 Citation

If you use this dataset, please cite the associated publication (to be updated after acceptance).

Alternatively, you may cite the dataset directly using the DOI:

**DOI:** https://doi.org/10.5281/zenodo.19780148

```bibtex
@dataset{jarjis2026_smart_home_iot_fl_dataset,
  title={Smart-Home IoT Dataset for Federated Anomaly Detection},
  author={Jarjis, Alend and Becerikli, Yaşar},
  year={2026},
  doi={10.5281/zenodo.19780148},
  publisher={Zenodo}
}
📜 License



This dataset is licensed under the Creative Commons Attribution 4.0 International (CC BY 4.0).



Full license:

https://creativecommons.org/licenses/by/4.0/

\---

🤖 Declaration of Generative AI Usage



During the preparation of this repository and associated manuscript, generative AI tools (including ChatGPT) were used to assist with text drafting and documentation refinement. All generated content was reviewed and validated by the authors.

\---

📬 Contact



For questions or collaboration:



Alend Jarjis

Email: alend.jarjis@su.edu.krd

Alternative: alendhassan63@gmail.com



