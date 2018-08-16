# webcam-dashboard
Webcam data dashboard created for HealthMatters project

 ```
 docker build -t dash .
 docker run --rm -v "/media/HealthMattersShare/HealthMatters/Image analysis/All_Processed_Labels/export.csv":/export.csv -it --name dashtest -p 8050:8050 dash
 ```
