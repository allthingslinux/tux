-- Create the trigger function
CREATE OR REPLACE FUNCTION increment_note_number() RETURNS TRIGGER AS $$
DECLARE
    new_note_number INT;
BEGIN
    SELECT COALESCE(MAX(note_number), 0) + 1 INTO new_note_number
    FROM "Note"
    WHERE guild_id = NEW.guild_id;

    NEW.note_number = new_note_number;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create the trigger
CREATE TRIGGER set_note_number
BEFORE INSERT ON "Note"
FOR EACH ROW
EXECUTE FUNCTION increment_note_number();
