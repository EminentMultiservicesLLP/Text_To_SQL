def validate(sql):

    banned = ["DROP", "DELETE", "TRUNCATE", "ALTER"]

    for word in banned:
        if word in sql.upper():
            raise Exception("Dangerous query blocked")

    return sql