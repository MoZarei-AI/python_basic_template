import logging, time
from python_basic_template.data_handler.load_data import load_raw_data


logger = logging.getLogger(__name__)



def main():
    start = time.time()
    logger.info("Starting data preparation...")
    df = load_raw_data('example.csv')
    print(df.head())
    

    end = time.time()
    logger.info(f"Data preparation completed in {end - start:.2f} seconds.")


if __name__ == "__main__":
    main()