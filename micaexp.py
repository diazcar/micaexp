import argparse

from src.routines.xair import (
    DATA_KEYS,
    wrap_xair_request,
    )

from src.fonctions import (
    list_of_strings,
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="micaexp.py",
        description="""
        This is a python plotly-dash application to explore and
        compare microcaptor and reference stations
        """,
        epilog="Author :  Carlos DIAZ, Atmosud."
    )
    parser.add_argument(
        "-sd", "--start_date",
        metavar="\b",
        type=str,
        help="""
        Start date  in YYYY-MM-DDThh:mm:ss format
        """
    )
    parser.add_argument(
        "-ed", "--end_date",
        metavar="\b",
        type=str,
        help="""
        End date in YYYY-MM-DDThh:mm:ss format
        """
    )
    parser.add_argument(
        "-mc", "--micro_capteur_id",
        metavar="\b",
        type=list_of_strings,
        help="""
        List of micro capteurs id's to retrive
        """
    )
    parser.add_argument(
        "-rs", "--reference_stations",
        metavar="\b",
        type=list_of_strings,
        help="""
        List of reference stations to compare
        """,
        default=["NCA"]
    )
    parser.add_argument(
        "-iso", "--poll_iso",
        metavar="\b",
        type=list_of_strings,
        help="""
        List of pollutant iso in {PM10:24, PM2.5:39 ,PM1:68}
        """,
        default="24"
    )
    parser.add_argument(
        "-o", "--output",
        metavar="\b",
        type=str,
        help=""",
        Output path for csv file
        """,
        default="./",
    )
    parser.add_argument(
        "-n", "--name",
        metavar="\b",
        type=str,
        help=""",
        Name of the outputfile
        """,
        default="xair_data",
    )

    args = parser.parse_args()

    xair_data = wrap_xair_request(
            fromtime=args.start_date,
            totime=args.end_date,
            keys=DATA_KEYS,
            sites=args.reference_stations,
            physicals=args.poll_iso,
    )

    xair_data.to_csv(f"{args.output}/{args.name}.csv")

