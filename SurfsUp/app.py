# Import the dependencies.
from matplotlib import style
style.use('fivethirtyeight')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
Base = automap_base()
Base.prepare(engine, reflect=True)
Measurement = Base.classes.measurement
Station = Base.classes.station
session = Session(engine)


#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################


@app.route("/")
def home():
    return (
        f"Welcome to the Hawaii Climate Analysis API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start<br/>"
        f"/api/v1.0/start/end<br/>"
        f"<p>'start' and 'end' date should be in the format YYYY-MM-DD.</p>" 
    )


@app.route("/api/v1.0/precipitation")
def precipitation():
    # Calculate the date one year ago from the last date in the database
    latest_date = session.query(func.max(Measurement.date)).scalar()
    latest_date = dt.datetime.strptime(latest_date, "%Y-%m-%d").date()
    one_year_ago = latest_date - dt.timedelta(days=365)

    # Query for precipitation data
    precipitation_data = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date >= one_year_ago).all()

    session.close()

    # Create a dictionary from the query results
    precip = {date: prcp for date, prcp in precipitation_data}

    return jsonify(precip)


@app.route("/api/v1.0/stations")
def stations():
    results = session.query(Station.station).all()
    session.close()

    all_stations = list(np.ravel(results))
    return jsonify(all_stations)


@app.route("/api/v1.0/tobs")
def tobs():
    # Query to find most active stations
    results = (
        session.query(Station.station, func.count(Measurement.station).label('measurement_count'))
        .join(Measurement, Station.station == Measurement.station)
        .group_by(Station.station)
        .order_by(func.count(Measurement.station).desc())
        .all()
    )
    most_active_station = results[0][0]

    # Calculate the date one year ago from the last date in data set.
    latest_date = session.query(func.max(Measurement.date)).filter(Measurement.station == most_active_station).scalar()
    latest_date = dt.datetime.strptime(latest_date, "%Y-%m-%d").date()
    one_year_ago = latest_date - dt.timedelta(days=365)


    # Query the last 12 months of temperature observation data for this station
    results = session.query(Measurement.tobs).\
        filter(Measurement.station == most_active_station).\
        filter(Measurement.date >= one_year_ago).all()

    # Extract temperature observations from the query result
    temperatures = [result[0] for result in results]
    session.close()

    return jsonify(temperatures)



# Fetch data from the Measurement table
measurement_data = session.query(Measurement.station, Measurement.tobs, Measurement.date).all()


@app.route("/api/v1.0/<start>")
def start_date(start):
    """Return the min, avg, and max temperatures for all dates greater than or equal to the start date."""
    try:
        start_date = dt.datetime.strptime(start, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    # Query for temperature data across all stations
    results = session.query(
        func.min(Measurement.tobs),
        func.avg(Measurement.tobs),
        func.max(Measurement.tobs)
    ).filter(Measurement.date >= start_date).all()

    if not results:
        return jsonify({"error": "No temperature data found for the given start date."}), 404

    temp_stats = {"TMIN": results[0][0], "TAVG": results[0][1], "TMAX": results[0][2]}
    return jsonify(temp_stats)


@app.route("/api/v1.0/<start>/<end>")
def start_end_date(start, end):
    """Return the min, avg, and max temperatures for the dates between the start and end dates inclusive."""
    try:
        start_date = dt.datetime.strptime(start, "%Y-%m-%d").date()
        end_date = dt.datetime.strptime(end, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    # Query for temperature data across all stations
    results = session.query(
        func.min(Measurement.tobs),
        func.avg(Measurement.tobs),
        func.max(Measurement.tobs)
    ).filter(Measurement.date >= start_date).filter(Measurement.date <= end_date).all()

    if not results:
        return jsonify({"error": "No temperature data found for the given date range."}), 404

    temp_stats = {"TMIN": results[0][0], "TAVG": results[0][1], "TMAX": results[0][2]}
    return jsonify(temp_stats)


if __name__ == "__main__":
    app.run(debug=True)