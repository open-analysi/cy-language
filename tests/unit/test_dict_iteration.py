"""
TDD Test: Add support for iterating over dictionaries in for-in loops.

Expected behavior (matching Python/JavaScript):
  for (key in my_dict) { ... }

Should iterate over the KEYS of the dictionary.
"""

from cy_language import Cy


class TestDictIteration:
    """Test that for-in loops work with dictionaries."""

    def test_iterate_over_dict_keys(self):
        """
        Verify that iterating over a dict yields keys (like Python/JavaScript).
        """
        script = """
all_users = {
    "cn=user1,dc=example,dc=com": True,
    "cn=user2,dc=example,dc=com": True
}

key_list = []
for (user_dn in all_users) {
    key_list = key_list + [user_dn]
}

return join(key_list, "|")
"""

        cy = Cy()
        result = cy.run(script, {})

        # Should return the keys joined
        assert "cn=user1,dc=example,dc=com" in result
        assert "cn=user2,dc=example,dc=com" in result

    def test_iterate_dict_simple(self):
        """Test simple dict iteration."""
        script = """
data = {"name": "Alice", "age": "30", "city": "NYC"}
key_list = []

for (key in data) {
    key_list = key_list + [key]
}

return join(key_list, ", ")
"""

        cy = Cy()
        result = cy.run(script, {})

        # Should contain all three keys
        assert "name" in result
        assert "age" in result
        assert "city" in result

    def test_iterate_dict_access_values(self):
        """Test iterating dict and accessing values."""
        script = """
scores = {"Alice": 95, "Bob": 87, "Carol": 92}
results = []

for (name in scores) {
    score = scores[name]
    results = results + ["${name}: ${score}"]
}

return join(results, ", ")
"""

        cy = Cy()
        result = cy.run(script, {})

        assert "Alice: 95" in result
        assert "Bob: 87" in result
        assert "Carol: 92" in result

    def test_iterate_empty_dict(self):
        """Test iterating over empty dictionary."""
        script = """
data = {}
count = 0

for (key in data) {
    count = count + 1
}

return count
"""

        cy = Cy()
        result = cy.run(script, {})
        assert result == "0"

    def test_dict_iteration_preserves_key_order(self):
        """Test that dict iteration preserves insertion order (Python 3.7+)."""
        script = """
data = {"first": 1, "second": 2, "third": 3}
key_list = []

for (key in data) {
    key_list = key_list + [key]
}

return join(key_list, ",")
"""

        cy = Cy()
        result = cy.run(script, {})

        # Python 3.7+ dicts preserve insertion order
        assert result == '"first,second,third"'

    def test_nested_dict_iteration(self):
        """Test nested dict iteration."""
        script = """
users = {
    "alice": {"role": "admin"},
    "bob": {"role": "user"}
}

roles = []
for (username in users) {
    user_data = users[username]
    role = user_data["role"]
    roles = roles + ["${username}:${role}"]
}

return join(roles, ",")
"""

        cy = Cy()
        result = cy.run(script, {})

        assert "alice:admin" in result
        assert "bob:user" in result
