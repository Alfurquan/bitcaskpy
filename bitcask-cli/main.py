import bitcaskpy

def main():
    db = bitcaskpy.open_store("data")
    db.put("Key1", "Value1")
    db.put("Key2", "Value2")
    print(db.get("Key1"))
    print(db.get("Key2"))
    db.delete("Key1")
    print(db.get("Key1"))  # Should return None or indicate that the key does not exist

if __name__ == "__main__":
    main()