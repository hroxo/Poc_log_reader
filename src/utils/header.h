#ifndef HEADER_H
# define HEADER_H

# include <ctype.h> // For isspace
# include <signal.h> // For sig_atomic_t
# include <stdio.h>
# include <stdlib.h>
# include <string.h>
# include <unistd.h>
# include <fcntl.h>
# include <time.h> // For timestamp generation
# include <sys/inotify.h> // For inotify file monitoring
# include <poll.h> // For poll()

# define BUFFER_SIZE 8192 // For get_next_line

// Structure to hold extracted log data
typedef struct s_log_data
{
    char    *description;
    char    *upc;
    int     item_number;
    int     price;
    int     quantity;
    int     discount_amount;
    int     total_amount;
    int     balance_due;
    int     item_count;
    char    *tender_type;
    char    *discount_description;
    int     amount; // For TenderAccepted
}               t_log_data;

typedef struct s_log_entry
{
    char        *timestamp;
    char        *event_type;
    t_log_data  *data; // Pointer to a struct containing event-specific data
}               t_log_entry;

// get_next_line functions
char    *get_next_line(int fd);
void	*ft_glcalloc(size_t nmemb, size_t size);
size_t	ft_glstrlen(char *str);
char	*ft_glstrjoin(char *s1, char *s2);
size_t	has_nl(char *str);


// log_reader.c functions
void    start_monitoring(const char *log_file_path);

// info_extractor.c functions
t_log_entry *extract_info(const char *log_line);
char    *extract_field_value(const char *xml_string, const char *field_name);
char    *extract_message_id(const char *xml_string);
char    *extract_timestamp(const char *log_line);
void    trim_whitespace(char *str);

// info_convert.c functions
void    convert_to_json(t_log_entry *entry, FILE *output_file);

// Utility functions for memory management
void    free_log_entry(t_log_entry *entry);
void    free_log_data(t_log_data *data);

#endif
