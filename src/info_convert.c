#include "utils/header.h"

static void	append_buf(char **buf, size_t *size, size_t *len, const char *str)
{
	size_t	str_len;

	str_len = strlen(str);
	if (*len + str_len + 1 > *size)
	{
		*size = (*size + str_len + 1) * 2;
		*buf = (char *)realloc(*buf, *size);
		if (!*buf)
		{
			perror("realloc failed");
			exit(EXIT_FAILURE);
		}
	}
	memcpy(*buf + *len, str, str_len);
	*len += str_len;
	(*buf)[*len] = '\0';
}

static void	add_str(char **buf, size_t *sz, size_t *ln,
	const char *key, const char *val, int *first)
{
	char	tmp[512];

	if (!val)
		return ;
	if (!*first)
		append_buf(buf, sz, ln, ",");
	*first = 0;
	snprintf(tmp, sizeof(tmp), "\"%s\":\"%s\"", key, val);
	append_buf(buf, sz, ln, tmp);
}

static void	add_int(char **buf, size_t *sz, size_t *ln,
	const char *key, int val, int *first)
{
	char	tmp[128];

	if (!*first)
		append_buf(buf, sz, ln, ",");
	*first = 0;
	snprintf(tmp, sizeof(tmp), "\"%s\":%d", key, val);
	append_buf(buf, sz, ln, tmp);
}

static void	build_item_sold(t_log_entry *e, char **b, size_t *sz, size_t *ln)
{
	int	first;

	first = 1;
	add_str(b, sz, ln, "description", e->data->description, &first);
	add_str(b, sz, ln, "upc", e->data->upc, &first);
	if (e->data->price > 0)
		add_int(b, sz, ln, "price", e->data->price, &first);
	if (e->data->quantity > 0)
		add_int(b, sz, ln, "quantity", e->data->quantity, &first);
}

static void	build_discount(t_log_entry *e, char **b, size_t *sz, size_t *ln)
{
	int	first;

	first = 1;
	add_str(b, sz, ln, "upc", e->data->upc, &first);
	if (e->data->discount_amount != 0)
		add_int(b, sz, ln, "discount_amount",
			e->data->discount_amount, &first);
	add_str(b, sz, ln, "discount_description",
		e->data->discount_description, &first);
}

static void	build_totals(t_log_entry *e, char **b, size_t *sz, size_t *ln)
{
	int	first;

	first = 1;
	if (e->data->total_amount != 0)
		add_int(b, sz, ln, "total_amount",
			e->data->total_amount, &first);
	if (e->data->item_count != 0)
		add_int(b, sz, ln, "item_count", e->data->item_count, &first);
	if (e->data->balance_due != 0)
		add_int(b, sz, ln, "balance_due",
			e->data->balance_due, &first);
}

static void	build_tender(t_log_entry *e, char **b, size_t *sz, size_t *ln)
{
	int	first;

	first = 1;
	if (e->data->amount != 0)
		add_int(b, sz, ln, "amount", e->data->amount, &first);
	add_str(b, sz, ln, "tender_type", e->data->tender_type, &first);
	add_str(b, sz, ln, "description", e->data->description, &first);
}

void	convert_to_json(t_log_entry *entry, FILE *output_file)
{
	char	*buf;
	size_t	sz;
	size_t	ln;
	int		written;

	if (!entry || !entry->timestamp || !entry->event_type)
		return ;
	sz = BUFFER_SIZE * 2;
	buf = (char *)malloc(sz);
	if (!buf)
		return ;
	written = snprintf(buf, sz, "{\"timestamp\":\"%s\",\"event_type\":\"%s\","
			"\"data\":{", entry->timestamp, entry->event_type);
	ln = (written > 0) ? (size_t)written : 0;
	if (strcmp(entry->event_type, "ItemSold") == 0)
		build_item_sold(entry, &buf, &sz, &ln);
	else if (strcmp(entry->event_type, "Discount") == 0)
		build_discount(entry, &buf, &sz, &ln);
	else if (strcmp(entry->event_type, "Totals") == 0)
		build_totals(entry, &buf, &sz, &ln);
	else if (strcmp(entry->event_type, "TenderAccepted") == 0)
		build_tender(entry, &buf, &sz, &ln);
	append_buf(&buf, &sz, &ln, "}}\n");
	fwrite(buf, 1, ln, stdout);
	if (output_file)
	{
		fwrite(buf, 1, ln, output_file);
		fflush(output_file);
	}
	free(buf);
}
