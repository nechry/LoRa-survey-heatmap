'use strict';

const minimist = require('minimist');
const fs = require('fs');
const { exit } = require('process');
const { parse } = require('csv-parse');
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

const inputFile = args.data;

const fileContent = fs.readFileSync(inputFile, { encoding: 'latin1' });
console.info(`Survey file ${inputFile} opened successfully!`)


const headers = ['Time', 'Compteur', 'rssi', 'rssi_min', 'rssi_max', 'snr', 'snr_min', 'snr_max', 'gateway_rssi', 'gateway_snr', 'Point', 'x', 'y', 'spreadingFactor'];

parse(fileContent, {
    delimiter: ';',
    columns: headers,
    fromLine: 2,
}, async (error, measurements) => {
    if (error) {
        console.error(error);
    }

    const survey_points = [];
    for (const measurement of measurements) {
        if (measurement.Compteur) {
            survey_points.push(
                {
                    counter: measurement.Compteur,
                    result: {
                        rssi: parseFloat(measurement.rssi),
                        snr: parseFloat(measurement.snr),
                        rssi_min: parseFloat(measurement.rssi_min),
                        snr_min: parseFloat(measurement.snr_min),
                        rssi_max: parseFloat(measurement.rssi_max),
                        snr_max: parseFloat(measurement.snr_max),
                        gateway_rssi: parseFloat(measurement.gateway_rssi),
                        gateway_snr: parseFloat(measurement.gateway_snr)
                    },
                    x: parseFloat(measurement.x),
                    y: parseFloat(measurement.y),
                }
            );
        }
    }

    const result = {
        title: "Sample Survey",
        img_path: "images/Sample Plan.png",
        survey_points,
    };


    const outputFile = "../data/Sample.json";
    // write CSV to a file
    fs.writeFileSync(outputFile, JSON.stringify(result), { encoding: "utf-8" });
    console.info(`Export file ${outputFile} saved!`);
    exit(0);

});