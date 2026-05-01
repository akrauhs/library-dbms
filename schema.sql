create table IF NOT EXISTS Genres (
    gid integer primary key autoincrement,
    name text not null unique
);

create TABLE IF NOT EXISTS Locations (
    lid integer primary key autoincrement,
    name text not null unique,
    address text
);

create table IF NOT EXISTS Members (
    mid integer primary key autoincrement,
    name text not null,
    email text not null unique,
    phone text
);

create table IF NOT EXISTS Books (
    bid integer primary key autoincrement,
    title text not null,
    author text not null,
    isbn text unique,
    gid integer references Genres(gid),
    lid integer references Locations(lid),
    copies integer default 1,
    available integer default 1
);

create table if not exists Borrowing (
    borrow_id integer primary key autoincrement,
    mid integer references Members(mid),
    bid integer references Books(bid),
    borrow_date date not null default (date('now')),
    due_date date not null default (date('now', '+14 day')),
    return_date date,
    status text not null default 'borrowed'
);

create index if not exists idx_borrowing_mid on Borrowing(mid);
create index if not exists idx_borrowing_bid on Borrowing(bid);
create index if not exists idx_books_gid on Books(gid);
create index if not exists idx_books_lid on Books(lid);
create index if not exists idx_borrowing_dates on Borrowing(borrow_date, due_date);

create trigger if not exists trg_checkout
after insert on Borrowing
begin
    update Books set available = available - 1 where bid = new.bid;
end;

create trigger if not exists trg_return
after update of return_date on Borrowing
begin
    update Books set available = available + 1 where bid = new.bid;
end;