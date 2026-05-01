from suit import task_result_verification
import time


# MAKE SURE THAT FIRST YOU HAVE RUN THE MAKE FILE !!!
# make -C my_Solutions\S03E04


result = task_result_verification(
    task_name="negotiations",
    answer={"tools": [
      {
        "URL": "https://legiocybernetica.uk/api/v1/S03E04-tool",
        "description": "Stock DB query tool. Schema: stock(item_name, item_code, city_name, city_code). Find cities selling an item by name fragment, or cities stocking all given item codes simultaneously. Natural language input. Request: {\"params\": \"<question>\"}. Response: {\"output\": \"<answer>\"}."
      }
    ]}
)

print(result)

# give him a couple of seconds:
time.sleep(15)

result = task_result_verification(
    task_name="negotiations",
    answer={"action": "check"}
)

print(result)


