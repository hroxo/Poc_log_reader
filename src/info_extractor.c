#include "utils/header.h"

// Helper to safely allocate and copy a string
static char *safe_strdup(const char *s) {
    if (!s) return NULL;
    return strdup(s);
}

// Helper to extract string values from XML fields
char *extract_field_value(const char *xml_string, const char *field_name) {
    char *start_tag;
    char *end_tag;
    char *value_start;
    char *result = NULL;
    char search_tag[256];

    // Construct the field start tag: <field ... name="FIELD_NAME">
    snprintf(search_tag, sizeof(search_tag), "name=\"%s\">", field_name);
    start_tag = strstr(xml_string, search_tag);

    if (start_tag) {
        value_start = start_tag + strlen(search_tag);
        end_tag = strstr(value_start, "</field>");
        if (end_tag) {
            size_t len = end_tag - value_start;
            result = (char *)malloc(len + 1);
            if (result) {
                strncpy(result, value_start, len);
                result[len] = '\0';
                trim_whitespace(result);
            }
        }
    }
    return result;
}

// Helper to extract integer values from XML fields
static int extract_int_field_value(const char *xml_string, const char *field_name) {
    char *str_value = extract_field_value(xml_string, field_name);
    int value = 0;
    if (str_value) {
        value = atoi(str_value);
        free(str_value);
    }
    return value;
}

// Helper to extract message id or name
char *extract_message_id(const char *xml_string) {
    char *id_start = strstr(xml_string, "id=\"");
    char *name_start = strstr(xml_string, "name=\"");
    char *start = NULL;
    char *end = NULL;
    char *result = NULL;

    // Prioritize 'id' attribute if both exist
    if (id_start) {
        start = id_start + strlen("id=\"");
    } else if (name_start) {
        start = name_start + strlen("name=\"");
    }

    if (start) {
        end = strchr(start, '"');
        if (end) {
            size_t len = end - start;
            result = (char *)malloc(len + 1);
            if (result) {
                strncpy(result, start, len);
                result[len] = '\0';
            }
        }
    }
    return result;
}

char *extract_timestamp(const char *log_line) {
    char *ts_start = strchr(log_line, '[');
    char *ts_end;
    char *timestamp_str = NULL;

    if (ts_start) {
        ts_end = strchr(ts_start + 1, ']');
        if (ts_end) {
            size_t len = ts_end - ts_start - 1;
            timestamp_str = (char *)malloc(len + 1);
            if (timestamp_str) {
                strncpy(timestamp_str, ts_start + 1, len);
                timestamp_str[len] = '\0';
            }
        }
    }
    return timestamp_str;
}

void trim_whitespace(char *str) {
    char	*start;
    char	*end;
    size_t	len;

    if (str == NULL || *str == '\0')
        return;
    start = str;
    while (isspace((unsigned char)*start))
        start++;
    if (*start == '\0')
    {
        str[0] = '\0';
        return;
    }
    end = start + strlen(start) - 1;
    while (end > start && isspace((unsigned char)*end))
        end--;
    len = (size_t)(end - start + 1);
    if (start != str)
        memmove(str, start, len);
    str[len] = '\0';
}

t_log_entry *extract_info(const char *log_line) {
    t_log_entry *entry = (t_log_entry *)ft_glcalloc(1, sizeof(t_log_entry));
    if (!entry) return NULL;

    entry->data = (t_log_data *)ft_glcalloc(1, sizeof(t_log_data));
    if (!entry->data) {
        free(entry);
        return NULL;
    }

    entry->timestamp = extract_timestamp(log_line);
    
    char *message_start = strstr(log_line, "<message");
    if (!message_start) {
        free_log_entry(entry);
        return NULL;
    }

    entry->event_type = extract_message_id(message_start);
    if (!entry->event_type) {
        // Handle one-liner assist mode messages
        if (strstr(log_line, "<message name=\"EnterAssistMode\"")) {
            entry->event_type = safe_strdup("EnterAssistMode");
        } else if (strstr(log_line, "<message name=\"ExitAssistMode\"")) {
            entry->event_type = safe_strdup("ExitAssistMode");
        }
    }

    // Detect EnteredStoreMode sent as a Command message with Command.1 field
    if (entry->event_type && strcmp(entry->event_type, "Command") == 0) {
        if (strstr(log_line, "ftype=\"string\">EnteredStoreMode</field>")) {
            free(entry->event_type);
            entry->event_type = safe_strdup("EnteredStoreMode");
        }
    }

    if (!entry->event_type) {
        free_log_entry(entry);
        return NULL;
    }

    if (strcmp(entry->event_type, "ItemSold") == 0) {
        entry->data->discount_amount = extract_int_field_value(message_start, "DiscountAmount");
        if (entry->data->discount_amount > 0) {
            free(entry->event_type);
            entry->event_type = safe_strdup("Discount");
            entry->data->upc = extract_field_value(message_start, "UPC");
            entry->data->discount_description = extract_field_value(message_start, "DiscountDescription.1");
        } else {
            entry->data->description = extract_field_value(message_start, "Description");
            entry->data->upc = extract_field_value(message_start, "UPC");
            entry->data->item_number = extract_int_field_value(message_start, "ItemNumber");
            entry->data->price = extract_int_field_value(message_start, "Price");
            entry->data->quantity = extract_int_field_value(message_start, "Quantity");
        }
    } else if (strcmp(entry->event_type, "Totals") == 0) {
        entry->data->total_amount = extract_int_field_value(message_start, "TotalAmount");
        entry->data->balance_due = extract_int_field_value(message_start, "BalanceDue");
        entry->data->item_count = extract_int_field_value(message_start, "ItemCount");
    } else if (strcmp(entry->event_type, "TenderAccepted") == 0) {
        entry->data->amount = extract_int_field_value(message_start, "Amount");
        entry->data->tender_type = extract_field_value(message_start, "TenderType");
        entry->data->description = extract_field_value(message_start, "Description");
    }
    // StartTransaction and EndTransaction have no specific data fields to extract for now

    return entry;
}

void free_log_data(t_log_data *data) {
    if (!data) return;
    free(data->description);
    free(data->upc);
    free(data->tender_type);
    free(data->discount_description);
    free(data);
}

void free_log_entry(t_log_entry *entry) {
    if (!entry) return;
    free(entry->timestamp);
    free(entry->event_type);
    free_log_data(entry->data);
    free(entry);
}
