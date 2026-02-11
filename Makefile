NAME = sco_monitor
CC= cc
CFLAGS= -Wall -Werror -Wextra -O2

SRCS = 	src/main.c \
		src/log_reader.c \
		src/info_extractor.c \
		src/info_convert.c \
		src/get_next_line_bonus.c \
		src/get_next_line_utils_bonus.c

OBJS = $(SRCS:.c=.o)

RM = rm -rf

all: $(NAME)

%.o: %.c
	$(CC) $(CFLAGS) -Isrc/utils -c $< -o $@

$(NAME): $(OBJS)
	$(CC) $(CFLAGS) $(OBJS) -Isrc/utils -o $(NAME) 

clean: 
	$(RM) $(OBJS)

fclean: clean
	$(RM) $(NAME)

re: fclean all

.PHONY: all clean fclean re