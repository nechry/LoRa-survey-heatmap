'use strict';

const minimist = require('minimist');
const fs = require('fs');
const { exit } = require('process');

const converter = require('json-2-csv');

let args = minimist(process.argv.slice(2), {
    string: 'data',   
    default: {
        title: "LoRaWAN Survey",
        locations: "[0,0,0,0]"
    },
});

if (!args.data) {
    console.log('Please provide a data file with argument --data [file_path.json]');
    exit(-1)
}


const survey_file =args.data;
const title = args.title;
const locations = [];

args.locations.replace('[','').replace(']','').split(',').forEach(point => {
    locations.push(parseInt(point));
});

const survey_result = [];

fs.readFile(survey_file, (err, data) => {
    if (err) throw err;
    let measurements = JSON.parse(data);

    measurements.forEach(measurement => {    
        if (measurement.result.rssi && measurement.result.snr) {
            let survey_data = {
                time: new Date(measurement.time).toLocaleTimeString('fr-CH'),
                counter: measurement.counter,
                rssi: parseInt(measurement.result.rssi),
                snr: parseFloat(measurement.result.snr),
                x: 0,
                y: 0,
                gateway_rssi: parseInt(measurement.gateway.rssi),
                gateway_snr: parseFloat(measurement.gateway.snr),
                spreadingFactor: measurement.result.spreadingFactor 
            };
            survey_result.push(survey_data);
        }
    });

    const options = {
        checkSchemaDifferences: true,
        delimiter: {
            field: ";"
        }
    };
    // convert JSON array to CSV string
    converter.json2csv(survey_result, options, (err, csvContent) => {
        if (err) {
            throw err;
        }

        const outputFile = "survey.csv";
        // write CSV to a file
        fs.writeFileSync(outputFile, csvContent, { encoding: "utf-8" });
        console.info(`Export file ${outputFile} saved!`);
        exit(0);
    });
});
